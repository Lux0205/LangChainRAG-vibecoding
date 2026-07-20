"""直接测试智谱API"""
import httpx
import json
import os, dotenv

# 加载配置
dotenv.load_dotenv(".env")
api_key = os.getenv("ZHIPU_API_KEY")
model = os.getenv("ZHIPU_MODEL", "glm-4")

print(f"API Key: {api_key[:20]}...")
print(f"Model: {model}")

url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {
    "model": model,
    "messages": [{"role": "user", "content": "你好，请用一句话介绍你自己"}],
    "max_tokens": 100,
    "stream": False  # 先测试非流式
}

print("\n测试非流式调用...")
resp = httpx.post(url, headers=headers, json=payload, timeout=30)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:500]}")

# 测试流式
print("\n测试流式调用...")
payload["stream"] = True
resp = httpx.post(url, headers=headers, json=payload, timeout=30)
print(f"Status: {resp.status_code}")
print(f"Content-Type: {resp.headers.get('content-type', 'none')}")
print(f"Response: {resp.text[:500]}")
