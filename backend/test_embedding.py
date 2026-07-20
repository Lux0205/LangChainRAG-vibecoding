"""测试通义千问 Embedding + 检索流程"""
import asyncio
import sys

print("=" * 55)
print("  测试：通义千问 text-embedding-v1 向量检索")
print("=" * 55)

# 测试1: Embedding 连接
print("\n【测试1】调用 Dashscope Embedding API...")
from app.config import settings
print(f"  API Key: {settings.DASHSCOPE_API_KEY[:20]}...")
print(f"  Embedding模型: {settings.TONGYI_EMBEDDING_MODEL}")
print(f"  Embedding提供商: {settings.EMBEDDING_PROVIDER}")

from app.rag.embeddings import DashscopeEmbeddings
emb = DashscopeEmbeddings()

# 单条测试
test_text = "iPhone 15 Pro 手机价格"
vec = emb.embed_query(test_text)
print(f"  ✓ 单条 embedding 维度: {len(vec)}, 前5个值: {[round(v,4) for v in vec[:5]]}")

# 批量测试
texts = ["苹果手机价格", "华为手机多少钱", "小米手机配置", "MacBook Pro 笔记本电脑", "平台售后政策"]
vecs = emb.embed_documents(texts)
print(f"  ✓ 批量embedding {len(texts)} 条，全部为 {len(vecs[0])} 维")

# 测试2: 向量索引构建
print("\n【测试2】构建向量索引...")
from app.rag.vector_store import _build_index, get_collection_stats
_build_index()
stats = get_collection_stats()
print(f"  ✓ 索引统计: {stats}")

# 测试3: 语义检索
print("\n【测试3】语义检索测试...")
from app.rag.vector_store import similarity_search

questions = [
    "iPhone 15 Pro 多少钱？",
    "华为手机支持卫星通话吗？",
    "小米14的屏幕尺寸是多少？",
]

for q in questions:
    print(f"\n  🔍 问题: {q}")
    results = similarity_search(q, k=3)
    if results:
        for i, r in enumerate(results):
            title = r['metadata'].get('doc_title', '未知')
            score = r['score']
            content_preview = r['content'][:60].replace('\n', ' ')
            print(f"     [{i+1}] {title} | 相似度: {score:.4f} | {content_preview}...")
    else:
            print("     ⚠️ 未找到结果")

print("\n" + "=" * 55)
print("  测试完成！")
print("=" * 55)
