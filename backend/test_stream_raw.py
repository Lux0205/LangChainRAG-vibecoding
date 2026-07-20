"""看 dashscope 流式 API 原始返回"""
import dashscope
from app.config import settings

dashscope.api_key = settings.DASHSCOPE_API_KEY

print("原始流式返回:\n")
count = 0
for resp in dashscope.Generation.call(
    model=settings.TONGYI_MODEL,
    messages=[{"role": "user", "content": "说一句话：你好"}],
    result_format="message",
    stream=True,
    incremental_output=True,
):
    count += 1
    chunk = resp.output.choices[0].message.content
    print(f"chunk[{count}]: {repr(chunk)}")
    if count >= 20:
        break

print("\n\n--- 非累积模式，看增量 ---")
output_text = ""
for resp in dashscope.Generation.call(
    model=settings.TONGYI_MODEL,
    messages=[[{"role": "user", "content": "你好"}]],
    result_format="message",
    stream=True,
    incremental_output=True,
):
    chunk = resp.output.choices[0].message.content
    print(f"  原始chunk: {repr(chunk)}")
    if chunk.endswith(output_text) and len(chunk) >= len(output_text):
        new = chunk[:len(chunk)-len(output_text)] if output_text else chunk
    else:
        new = chunk
    output_text = chunk
    print(f"  新增: {repr(new)}")
    if len(output_text) > 50:
        break
