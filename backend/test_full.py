"""端到端测试：通义千问 Embedding + LLM 生成回答"""
import requests, json

print("=" * 55)
print("  端到端测试：通义千问 Embedding(+Tongyi LLM)")
print("=" * 55)

# 1. 登录
r = requests.post("http://localhost:8000/api/auth/login",
    json={"username": "admin", "password": "123456"}, timeout=10)
token = r.json()["access_token"]
print("\n1. 登录 ✓")

# 2. 创建会话
r = requests.post("http://localhost:8000/api/chat/sessions",
    headers={"Authorization": f"Bearer {token}"}, timeout=10)
sid = r.json()["id"]
print(f"2. 会话 ID={sid} ✓")

# 3. 测试1: 纯检索模式（none）
question = "iPhone 15 Pro 多少钱？"
print(f"\n3. 提问(纯检索模式): {question}")
print("-" * 55)

r = requests.post(
    f"http://localhost:8000/api/chat/chat?session_id={sid}&question={question}&provider=none",
    headers={"Authorization": f"Bearer {token}"},
    stream=True, timeout=30
)

full_text = ""
citations = []
for line in r.iter_lines():
    if line and line.startswith(b"data: "):
        data = json.loads(line[6:])
        if data.get("type") == "token":
            full_text += data["content"]
        elif data.get("type") == "citations":
            citations = data.get("data", [])
        elif data.get("type") == "done":
            break

print(full_text[:500])
print(f"引用: {len(citations)} 条")
for c in citations[:2]:
    print(f"   [{c['index']}] {c['doc_title']} (score: {c['score']:.2f})")

# 4. 测试2: 通义千问 LLM 模式
print("\n" + "=" * 55)
question2 = "华为Mate 60 Pro支持什么特殊功能？"
print(f"\n4. 提问(通义千问LLM): {question2}")
print("-" * 55)

# 重新创建会话
r = requests.post("http://localhost:8000/api/chat/sessions",
    headers={"Authorization": f"Bearer {token}"}, timeout=10)
sid2 = r.json()["id"]

r = requests.post(
    f"http://localhost:8000/api/chat/chat?session_id={sid2}&question={question2}&provider=tongyi",
    headers={"Authorization": f"Bearer {token}"},
    stream=True, timeout=60
)

full_text = ""
citations = []
for line in r.iter_lines():
    if line and line.startswith(b"data: "):
        data = json.loads(line[6:])
        if data.get("type") == "token":
            full_text += data["content"]
        elif data.get("type") == "citations":
            citations = data.get("data", [])
        elif data.get("type") == "done":
            break

print(full_text[:500])
print(f"引用: {len(citations)} 条")
for c in citations[:2]:
    print(f"   [{c['index']}] {c['doc_title']} (score: {c['score']:.2f})")

print("\n" + "=" * 55)
print("  测试完成！")
print("=" * 55)
