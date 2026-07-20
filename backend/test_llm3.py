"""测试自定义 TongyiChatModel 流式输出"""
import asyncio
from app.rag.chain import TongyiChatModel

async def test():
    llm = TongyiChatModel()
    prompt = """你是电商问答助手。参考资料：

[1] 来源: 华为Mate 60 Pro 产品说明
华为Mate 60 Pro 支持卫星通话功能，是全球首款支持卫星通话的大众智能手机。

用户问题：华为Mate 60 Pro支持什么特殊功能？

请用一句话回答："""

    print("流式回答: ", end="", flush=True)
    full = ""
    async for chunk in llm.astream(prompt):
        full += chunk.content
        print(chunk.content, end="", flush=True)
    print()
    print(f"\n[总 {len(full)} 字符]")

asyncio.run(test())
