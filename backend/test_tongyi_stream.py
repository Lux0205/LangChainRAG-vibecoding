"""测试通义千问原生 SDK 流式调用 (在 chat_service 内部)"""
import asyncio

async def test():
    from app.services.chat_service import ChatService
    from app.rag.vector_store import similarity_search

    search_results = similarity_search("华为Mate 60 Pro支持什么特殊功能？", k=3)

    print("流式输出:")
    full = ""
    async for token in ChatService._tongyi_stream(
        question="华为Mate 60 Pro支持什么特殊功能？",
        search_results=search_results,
        chat_history=[],
    ):
        full += token
        print(token, end="", flush=True)

    print(f"\n\n[完成：{len(full)} 字符]")

asyncio.run(test())
