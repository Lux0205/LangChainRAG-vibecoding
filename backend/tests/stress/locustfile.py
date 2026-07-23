"""
Locust 压力测试主文件
模拟用户登录 -> 创建会话 -> 发送聊天问题 -> 查看历史
"""
import json
import random
import sys
import os
import threading

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from locust import HttpUser, task, between, events
from config import (
    BASE_URL, QUESTIONS, USER_PREFIX, USER_PASSWORD
)

# 全局用户ID计数器（线程安全）
_user_counter = 0
_user_lock = threading.Lock()


def _get_next_user_id():
    """获取下一个用户ID（线程安全）"""
    global _user_counter
    with _user_lock:
        _user_counter += 1
        return _user_counter


class RAGUser(HttpUser):
    """
    模拟 RAG 系统用户
    - wait_time: 用户思考时间（模拟真实使用间隔）
    """
    wait_time = between(2, 5)
    host = BASE_URL

    def on_start(self):
        """每个虚拟用户启动时执行：登录 + 创建会话"""
        # 使用全局计数器作为用户名后缀
        self._my_id = _get_next_user_id()
        self.username = f"{USER_PREFIX}{self._my_id}"
        self.token = None
        self.session_id = None
        self._login()
        if self.token:
            self._create_session()

    def _login(self):
        """登录获取 Token"""
        try:
            with self.client.post(
                "/api/auth/login",
                json={"username": self.username, "password": USER_PASSWORD},
                catch_response=True,
                name="/api/auth/login",
                timeout=30
            ) as resp:
                if resp.status_code == 200:
                    data = resp.json()
                    self.token = data.get("access_token", "")
                    self.user_db_id = data.get("user_id", 0)
                    resp.success()
                else:
                    resp.failure(f"登录失败: {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            # 用户可能不存在，尝试注册
            self._register_and_login()

    def _register_and_login(self):
        """如果用户不存在，先注册再登录"""
        try:
            # 注册
            self.client.post(
                "/api/auth/register",
                json={"username": self.username, "password": USER_PASSWORD},
                name="/api/auth/register",
                timeout=10
            )
            # 再登录
            with self.client.post(
                "/api/auth/login",
                json={"username": self.username, "password": USER_PASSWORD},
                catch_response=True,
                name="/api/auth/login",
                timeout=30
            ) as resp:
                if resp.status_code == 200:
                    data = resp.json()
                    self.token = data.get("access_token", "")
                    self.user_db_id = data.get("user_id", 0)
                    resp.success()
                else:
                    resp.failure(f"登录失败(注册后): {resp.status_code}")
        except Exception as e:
            print(f"[Locust] 用户 {self.username} 注册/登录异常: {e}")

    def _create_session(self):
        """创建聊天会话"""
        try:
            with self.client.post(
                "/api/chat/sessions",
                headers={"Authorization": f"Bearer {self.token}"},
                catch_response=True,
                name="/api/chat/sessions",
                timeout=15
            ) as resp:
                if resp.status_code == 200:
                    data = resp.json()
                    self.session_id = data.get("id", 0)
                    resp.success()
                else:
                    resp.failure(f"创建会话失败: {resp.status_code}")
                    self.session_id = 0
        except Exception as e:
            print(f"[Locust] 创建会话异常: {e}")
            self.session_id = 0

    @task(5)  # 权重5：核心操作，聊天问答
    def chat_question(self):
        """发送聊天问题（SSE流式）"""
        if not self.session_id or not self.token:
            return

        question = random.choice(QUESTIONS)

        try:
            with self.client.post(
                "/api/chat/chat",
                params={"session_id": self.session_id, "question": question, "provider": "tongyi"},
                headers={"Authorization": f"Bearer {self.token}"},
                stream=True,
                catch_response=True,
                name="/api/chat/chat",
                timeout=120  # LLM 生成可能需要较长时间
            ) as resp:
                # 验证 SSE 流完整性
                got_token = False
                got_done = False
                got_citations = False

                if resp.status_code != 200:
                    resp.failure(f"HTTP {resp.status_code}")
                    return

                try:
                    for line in resp.iter_lines():
                        if line:
                            line_str = line.decode('utf-8', errors='ignore')
                            # 使用json安全解析，避免字符串匹配误判
                            if line_str.startswith("data: "):
                                try:
                                    data = json.loads(line_str[6:])
                                    msg_type = data.get("type", "")
                                    if msg_type == "token":
                                        got_token = True
                                    elif msg_type == "citations":
                                        got_citations = True
                                    elif msg_type == "done":
                                        got_done = True
                                except (json.JSONDecodeError, ValueError):
                                    pass  # 忽略非JSON行
                except Exception as e:
                    resp.failure(f"读取SSE流异常: {e}")
                    return

                if got_token and got_done:
                    resp.success()
                elif got_done:
                    resp.success()  # 只有done也算成功（可能是检索模式）
                else:
                    resp.failure(f"SSE流不完整: token={got_token}, done={got_done}")

        except Exception as e:
            # 超时等异常记录但不中断
            print(f"[Locust] 聊天异常: {type(e).__name__}: {e}")

    @task(1)  # 权重1：偶尔查看历史
    def view_history(self):
        """查看会话历史消息"""
        if not self.session_id or not self.token:
            return

        with self.client.get(
            f"/api/chat/sessions/{self.session_id}/messages",
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True,
            name="/api/chat/sessions/[id]/messages",
            timeout=15
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"查看历史失败: {resp.status_code}")

    @task(1)  # 权重1：偶尔查看会话列表
    def list_sessions(self):
        """获取会话列表"""
        if not self.token:
            return
        with self.client.get(
            "/api/chat/sessions",
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True,
            name="/api/chat/sessions",
            timeout=15
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"查看会话列表失败: {resp.status_code}")


# ==================== 事件钩子 ====================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始时打印配置信息"""
    print("=" * 60)
    print("  🚀 压力测试开始")
    print(f"  目标: {BASE_URL}")
    print(f"  并发用户: {environment.runner.target_user_count}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束时打印统计摘要"""
    stats = environment.runner.stats
    print("")
    print("=" * 60)
    print("  🛑 压力测试结束")
    print(f"  总请求数: {stats.total.num_requests}")
    print(f"  失败数: {stats.total.num_failures}")
    print(f"  错误率: {stats.total.fail_ratio * 100:.1f}%")
    print(f"  平均响应时间: {stats.total.avg_response_time:.0f}ms")
    print(f"  P50: {stats.total.get_response_time_percentile(0.50):.0f}ms")
    print(f"  P95: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"  P99: {stats.total.get_response_time_percentile(0.99):.0f}ms")
    print(f"  RPS: {stats.total.total_rps:.1f}")
    print("=" * 60)
