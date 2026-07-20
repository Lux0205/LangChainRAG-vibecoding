"""测试聊天组件"""
import asyncio
import sys

# 测试1: 向量检索
print("=" * 40)
print("测试1: TF-IDF 向量检索")
from app.rag.vector_store import similarity_search, _build_index
_build_index()
results = similarity_search("iPhone 15 Pro 多少钱", k=3)
print(f"找到 {len(results)} 条结果")
for i, r in enumerate(results[:2]):
    print(f"  [{i+1}] score={r['score']:.4f} | {r['content'][:60]}...")

# 测试2: LLM 生成
print("=" * 40)
print("测试2: LLM 生成（智谱GLM-4）")
from app.rag.chain import stream_chat, format_context, format_chat_history

async def test_stream():
    full = ""
    async for token in stream_chat(
        question="iPhone 15 Pro 多少钱",
        search_results=results[:3],
        chat_history=[],
    ):
        full += token
    print(f"回答: {full[:300]}")
    return full

answer = asyncio.run(test_stream())
print("=" * 40)
print("测试完成！")
