"""最终测试：纯检索模式对话"""
import requests, json

print("=" * 50)
print("  纯检索模式测试（不调用任何大模型API）")
print("=" * 50)

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

# 3. 发送问题（纯检索模式）
question = "iPhone 15 Pro 多少钱"
print(f"\n3. 提问: {question}")
print("-" * 50)

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

print(full_text)
print("-" * 50)
print(f"\n4. 引用来源: {len(citations)} 条")
for c in citations:
    print(f"   [{c['index']}] {c['doc_title']} (score: {c['score']:.2f})")

print("\n5. 测试 ✓ 完成!")
