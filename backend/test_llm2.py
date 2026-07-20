"""直接用 dashscope 原生 SDK 测试 LLM"""
import dashscope
from app.config import settings

dashscope.api_key = settings.DASHSCOPE_API_KEY

print("测试1: 非流式调用")
try:
    resp = dashscope.Generation.call(
        model=settings.TONGYI_MODEL,
        messages=[{"role": "user", "content": "你好，请用一句话介绍你自己"}],
        result_format="message",
    )
    print(f"  状态: {resp.status_code}")
    if resp.status_code == 200:
        print(f"  回答: {resp.output.choices[0].message.content}")
    else:
        print(f"  错误: {resp.code} - {resp.message}")
except Exception as e:
    print(f"  ❌ 异常: {e}")

print("\n测试2: 流式调用")
try:
    responses = dashscope.Generation.call(
        model=settings.TONGYI_MODEL,
        messages=[{"role": "user", "content": "你好"}],
        result_format="message",
        stream=True,
    )
    full = ""
    for resp in responses:
        if resp.status_code == 200:
            full += resp.output.choices[0].message.content
    print(f"  流式回答: {full}")
except Exception as e:
    print(f"  ❌ 异常: {e}")
