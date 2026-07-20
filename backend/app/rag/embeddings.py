"""
Embedding向量化 - 支持 TF-IDF（本地） 和 通义千问（云端API）
"""
from typing import List
import os
import os.path
import jieba
import numpy as np

from collections import Counter
import math
import re
from app.config import settings


class DashscopeEmbeddings:
    """
    通义千问云端Embedding模型
    - 需要网络调用API
    - 效果好，支持中文语义理解
    - 模型: text-embedding-v1 (1024维)
    """

    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or settings.TONGYI_EMBEDDING_MODEL
        self.api_key = api_key or settings.DASHSCOPE_API_KEY
        self._dimension = 1024  # text-embedding-v1 输出维度

    def _call_api(self, texts: List[str]) -> List[List[float]]:
        """调用Dashscope Embedding API"""
        import dashscope
        dashscope.api_key = self.api_key

        # API每次最多支持25条文本
        all_embeddings = []
        batch_size = 25

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                resp = dashscope.TextEmbedding.call(
                    model=self.model,
                    input=batch,
                )
                if resp.status_code == 200:
                    batch_embeddings = [item['embedding'] for item in resp.output['embeddings']]
                    all_embeddings.extend(batch_embeddings)
                else:
                    print(f"[Dashscope] API错误: {resp.code} - {resp.message}")
                    # 返回零向量作为fallback
                    all_embeddings.extend([[0.0] * self._dimension] * len(batch))
            except Exception as e:
                print(f"[Dashscope] 调用失败: {e}")
                all_embeddings.extend([[0.0] * self._dimension] * len(batch))

        return all_embeddings

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量文档向量化"""
        if not texts:
            return []
        print(f"[Dashscope] 向量化 {len(texts)} 条文本...")
        embeddings = self._call_api(texts)
        print(f"[Dashscope] 完成，输出维度: {self._dimension}")
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """单条查询向量化"""
        embeddings = self._call_api([text])
        return embeddings[0] if embeddings else [0.0] * self._dimension

    @property
    def vector_dim(self) -> int:
        return self._dimension


class TfidfEmbeddings:
    """
    基于 TF-IDF + jieba 分词的轻量级中文 Embedding
    - 完全离线，无需网络
    - 无需API Key，零成本
    - 效果足够用于小规模知识库检索
    """

    def __init__(self, vector_dim: int = 512):
        self.vector_dim = vector_dim
        self.vocabulary = {}
        self.idf = {}
        self.is_fitted = False
        # jieba 缓存目录→ 设置到 D 盘
        import jieba
        jieba.dt.tmp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "..", "temp")
        jieba.dt.tmp_dir = os.path.abspath(jieba.dt.tmp_dir)
        os.makedirs(jieba.dt.tmp_dir, exist_ok=True)

    def _tokenize(self, text: str) -> List[str]:
        """中文分词"""
        # 清洗文本
        text = re.sub(r'\s+', ' ', text.strip())
        # jieba分词
        words = list(jieba.cut(text))
        # 过滤停用词和单字
        stopwords = {'的', '了', '在', '是', '我', '有', '和', '就',
                     '不', '人', '都', '一', '一个', '上', '也', '很',
                     '到', '说', '要', '去', '你', '会', '着', '没有',
                     '看', '好', '自己', '这', '他', '她', '它', '们'}
        return [w for w in words if len(w) > 1 and w not in stopwords]

    def fit(self, texts: List[str]):
        """训练 IDF"""
        # 对所有文本分词
        doc_words = [self._tokenize(t) for t in texts]

        # 构建词汇表
        all_words = set()
        for words in doc_words:
            all_words.update(words)

        # 限制词汇表大小
        # 按词频排序，取前 vector_dim 个词
        word_freq = Counter()
        for words in doc_words:
            word_freq.update(words)

        top_words = [w for w, _ in word_freq.most_common(self.vector_dim)]
        self.vocabulary = {w: i for i, w in enumerate(top_words)}

        # 计算 IDF
        n_docs = len(doc_words)
        for word in self.vocabulary:
            n_appear = sum(1 for words in doc_words if word in words)
            self.idf[word] = math.log((n_docs + 1) / (n_appear + 1)) + 1

        self.is_fitted = True

    def _vectorize(self, text: str) -> List[float]:
        """将文本转为 TF-IDF 向量"""
        if not self.is_fitted:
            # 未训练时返回随机向量
            return list(np.random.randn(self.vector_dim) * 0.01)

        words = self._tokenize(text)
        vec = [0.0] * self.vector_dim

        if not words:
            return vec

        word_count = Counter(words)
        max_count = max(word_count.values()) if word_count else 1

        for word, count in word_count.items():
            if word in self.vocabulary:
                idx = self.vocabulary[word]
                tf = 0.5 + 0.5 * count / max_count  # 归一化TF
                vec[idx] = tf * self.idf[word]

        return vec

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量文档向量化"""
        # 首次调用时自动训练
        if not self.is_fitted:
            print(f"[TF-IDF] 自动训练，处理 {len(texts)} 条文本...")
            self.fit(texts)
            print(f"[TF-IDF] 词汇表大小: {len(self.vocabulary)}")

        return [self._vectorize(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        """单条查询向量化"""
        return self._vectorize(text)


class LocalEmbeddings:
    """本地中文Embedding模型（sentence-transformers）"""

    def __init__(self, model_name: str = "shibing624/text2vec-base-chinese"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


# 全局单例，避免重复训练
_tfidf_instance = None
_dashscope_instance = None


def get_embeddings(provider: str = None):
    """
    获取Embedding实例
    provider: "tongyi" 使用通义千问API, "local" 使用本地TF-IDF
    默认读取 settings.EMBEDDING_PROVIDER
    """
    global _tfidf_instance, _dashscope_instance

    if provider is None:
        provider = settings.EMBEDDING_PROVIDER

    if provider == "tongyi":
        if _dashscope_instance is None:
            _dashscope_instance = DashscopeEmbeddings()
        return _dashscope_instance
    else:
        if _tfidf_instance is None:
            _tfidf_instance = TfidfEmbeddings(vector_dim=512)
        return _tfidf_instance
