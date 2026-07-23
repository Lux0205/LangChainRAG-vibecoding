"""
压力测试配置
"""
import os

# ==================== 服务器配置 ====================
BASE_URL = os.environ.get("STRESS_TEST_URL", "http://localhost:8000")

# ==================== 并发配置 ====================
CONCURRENT_USERS = int(os.environ.get("STRESS_USERS", "100"))    # 并发用户数
RAMP_UP_TIME = int(os.environ.get("STRESS_RAMP", "10"))          # 启动加压时间（秒）
SPAWN_RATE = int(os.environ.get("STRESS_SPAWN", "10"))           # 每秒启动用户数
TEST_DURATION = int(os.environ.get("STRESS_DURATION", "60"))     # 测试持续时间（秒）

# ==================== 测试用户配置 ====================
USER_PREFIX = "stress_user_"      # 用户名前缀
USER_PASSWORD = "Test@1234"       # 统一测试密码
TOTAL_USERS = 100                 # 预注册用户数

# ==================== 测试问题池 ====================
QUESTIONS = [
    "iPhone 15 Pro 多少钱？",
    "华为Mate 60 Pro有什么功能？",
    "小米14屏幕尺寸多大？",
    "MacBook Pro 14寸重量多少？",
    "平台售后政策是什么？",
    "iPhone 15 Pro 支持5G吗？",
    "华为和小米哪个好？",
    "怎么申请退货？",
    "MacBook Pro 14寸价格是多少？",
    "小米14的电池容量多大？",
    "iPhone 15 Pro 有哪些颜色？",
    "华为Mate 60 Pro 支持卫星通话吗？",
    "小米14的芯片是什么？",
    "15天质量问题换货怎么操作？",
    "iPhone 15 Pro 128GB多少钱？",
]

# ==================== 输出配置 ====================
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")

# 确保目录存在
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
