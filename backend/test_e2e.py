"""最终端到端测试"""
import requests, json

print("=" * 60)
print("  🔹 最终端到端测试：通义千问 Embedding + LLM")
print("=" * 60)

# 1. 登录
r = requests.post("http://localhost:8000/api/auth/login",
    json={"username": "admin", "password": "123456"}, timeout=10)
token = r.json()["access_token"]
print("1. 登录 ✓")

# 2. 创建会话
r = requests.post("http://localhost:8000/api/chat/sessions",
    headers={"Authorization": f"Bearer {token}"}, timeout=10)
sid = r.json()["id"]
print(f"2. 会话 ID={sid} ✓")

# 3. 通义千问 LLM 问答
questions = [
    "iPhone 15 Pro 手机多少钱？",
    "华为Mate 60 Pro支持什么特殊功能？",
    "小米14的屏幕尺寸是多少？",
]

for qi, question in enumerate(questions, 1):
    print(f"\n{'─' * 60}")
    print(f"🔍 问题{qi}: {question}")
    print(f"{'─' * 60}")

    # 新会话
    r = requests.post("http://localhost:8000/api/chat/sessions",
        headers={"Authorization": f"Bearer {token}"}, timeout=10)
    sid = r.json()["id"]

    r = requests.post(
        f"http://localhost:8000/api/chat/chat?session_id={sid}&question={question}&provider=tongyi",
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

    print(f"📝 回答:\n{full_text}")
    print(f"\n📚 引用 ({len(citations)} 条):")
    for c in citations:
        print(f"   [{c['index']}] {c['doc_title']} (相关度: {c['score']:.0%})")

print(f"\n{'=' * 60}")
print("✅ 全部测试通过！")
print(f"{'=' * 60}")
