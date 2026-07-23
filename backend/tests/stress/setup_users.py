"""
预注册测试用户
避免注册成为压力测试的瓶颈
"""
import sys
import os
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import BASE_URL, USER_PREFIX, USER_PASSWORD, TOTAL_USERS


def setup_users(count=TOTAL_USERS):
    """批量注册测试用户"""
    print(f"=" * 50)
    print(f"  预注册 {count} 个测试用户")
    print(f"  目标: {BASE_URL}")
    print(f"=" * 50)

    success = 0
    skip = 0
    fail = 0

    start_time = time.time()

    for i in range(1, count + 1):
        username = f"{USER_PREFIX}{i}"
        try:
            resp = requests.post(
                f"{BASE_URL}/api/auth/register",
                json={"username": username, "password": USER_PASSWORD},
                timeout=10
            )
            if resp.status_code == 200:
                success += 1
            elif resp.status_code == 400 and "已存在" in resp.text:
                skip += 1
            else:
                fail += 1
                print(f"  [失败] {username}: {resp.status_code} - {resp.text[:100]}")
        except Exception as e:
            fail += 1
            print(f"  [异常] {username}: {e}")

        # 每10个打印进度
        if i % 10 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            print(f"  进度: {i}/{count} ({success}成功, {skip}跳过, {fail}失败) - {rate:.1f}用户/秒")

    elapsed = time.time() - start_time
    print(f"")
    print(f"完成！耗时 {elapsed:.1f}秒")
    print(f"  成功: {success}")
    print(f"  跳过(已存在): {skip}")
    print(f"  失败: {fail}")
    print(f"")

    # 验证登录
    print("验证登录...")
    try:
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": f"{USER_PREFIX}1", "password": USER_PASSWORD},
            timeout=10
        )
        if resp.status_code == 200:
            print("✅ 登录验证通过")
        else:
            print(f"❌ 登录验证失败: {resp.status_code}")
    except Exception as e:
        print(f"❌ 登录验证异常: {e}")

    return fail == 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="预注册压力测试用户")
    parser.add_argument("-n", "--count", type=int, default=TOTAL_USERS, help=f"用户数量 (默认{TOTAL_USERS})")
    args = parser.parse_args()
    setup_users(args.count)
