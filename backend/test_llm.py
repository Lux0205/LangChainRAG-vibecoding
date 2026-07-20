"""单独测试通义千问 LLM 调用"""
import asyncio

print("=" * 50)
print("测试：通义千问 LLM 流式调用")
print("=" * 50)

from app.config import settings
print(f"API Key: {settings.DASHSCOPE_API_KEY[:20]}...")
print(f"模型: {settings.TONGYI_MODEL}")

async def test():
    from app.rag.chain import stream_chat, format_context, format_chat_history
    from app.rag.vector_store import similarity_search

    print("\n1. 检索...")
    search_results = similarity_search("华为Mate 60 Pro支持什么特殊功能？", k=3)
    print(f"   找到 {len(search_results)} 条")
    for r in search_results[:1]:
        print(f"   分数: {r['score']:.2f}, 标题: {r['metadata'].get('doc_title','')}")

    print("\n2. LLM 流式生成...")
    full = ""
    chunk_count = 0
    try:
        async for token in stream_chat(
            question="华为Mate 60 Pro支持什么特殊功能？",
            search_results=search_results,
            chat_history=[],
            provider="tongyi",
        ):
            full += token
            chunk_count += 1
            if chunk_count <= 5:
                print(f"   token[{chunk_count}]: {repr(token[:50])}")
    except Exception as e:
        print(f"   ❌ 异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n3. 结果: 共 {chunk_count} 个 token, 总长 {len(full)} 字符")
    print(f"   内容: {full[:200]}")

asyncio.run(test())
