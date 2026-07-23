"""
对 stress/ 目录下可测试函数的单元测试
"""
import unittest
import sys
import os
import csv
import tempfile
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    BASE_URL, CONCURRENT_USERS, USER_PREFIX, USER_PASSWORD,
    TOTAL_USERS, QUESTIONS, RESULTS_DIR, REPORTS_DIR
)
from locustfile import _get_next_user_id
from analyze import setup_chinese_font, analyze_locust_stats, analyze_monitor_data


class TestConfig(unittest.TestCase):
    """config.py 配置测试"""

    def test_base_url_default(self):
        """默认 BASE_URL 应为 localhost:8000"""
        self.assertIn("8000", BASE_URL)

    def test_concurrent_users_positive(self):
        """并发用户数应为正整数"""
        self.assertGreater(CONCURRENT_USERS, 0)

    def test_user_prefix_not_empty(self):
        """用户名前缀不应为空"""
        self.assertTrue(len(USER_PREFIX) > 0)

    def test_password_not_empty(self):
        """密码不应为空"""
        self.assertTrue(len(USER_PASSWORD) > 0)

    def test_total_users_100(self):
        """预注册用户数应为100"""
        self.assertEqual(TOTAL_USERS, 100)

    def test_questions_not_empty(self):
        """问题池不应为空"""
        self.assertGreater(len(QUESTIONS), 0)

    def test_questions_all_chinese(self):
        """所有问题应为字符串且包含中文"""
        for q in QUESTIONS:
            self.assertIsInstance(q, str)
            self.assertGreater(len(q), 0)

    def test_results_dir_exists(self):
        """结果目录应已创建"""
        self.assertTrue(os.path.isdir(RESULTS_DIR))

    def test_reports_dir_exists(self):
        """报告目录应已创建"""
        self.assertTrue(os.path.isdir(REPORTS_DIR))


class TestGetNextUserId(unittest.TestCase):
    """locustfile.py - _get_next_user_id 线程安全计数器测试"""

    def setUp(self):
        """每个测试前重置计数器"""
        import locustfile
        locustfile._user_counter = 0

    def test_returns_incrementing_ids(self):
        """应返回递增的 ID"""
        import locustfile
        locustfile._user_counter = 0
        ids = [_get_next_user_id() for _ in range(10)]
        self.assertEqual(ids, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    def test_thread_safety(self):
        """多线程并发调用不应出现重复 ID"""
        import locustfile
        locustfile._user_counter = 0
        results = []
        errors = []

        def worker():
            try:
                for _ in range(100):
                    results.append(_get_next_user_id())
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"并发出错: {errors}")
        self.assertEqual(len(results), 1000)
        self.assertEqual(len(set(results)), 1000, "出现重复ID，线程不安全")

    def test_returns_int(self):
        """返回值应为整数"""
        import locustfile
        locustfile._user_counter = 0
        result = _get_next_user_id()
        self.assertIsInstance(result, int)

    def test_positive_values(self):
        """返回值应始终为正数"""
        import locustfile
        locustfile._user_counter = 0
        for _ in range(50):
            self.assertGreater(_get_next_user_id(), 0)


class TestSetupChineseFont(unittest.TestCase):
    """analyze.py - setup_chinese_font 测试"""

    def test_returns_bool(self):
        """应返回布尔值"""
        result = setup_chinese_font()
        self.assertIsInstance(result, bool)

    def test_returns_true_on_windows(self):
        """在 Windows 上应返回 True（有系统字体）"""
        if os.name == 'nt':
            result = setup_chinese_font()
            self.assertTrue(result)


class TestAnalyzeLocustStats(unittest.TestCase):
    """analyze.py - analyze_locust_stats 测试"""

    def setUp(self):
        """创建临时 CSV 文件"""
        self.temp_dir = tempfile.mkdtemp()

    def _create_stats_csv(self, rows):
        """创建临时 stats CSV"""
        path = os.path.join(self.temp_dir, "test_stats.csv")
        fieldnames = ["Type", "Name", "Request Count", "Failure Count",
                      "Median Response Time", "Average Response Time",
                      "Min Response Time", "Max Response Time",
                      "Average Content Size", "Requests/s", "Failures/s",
                      "50%", "66%", "75%", "80%", "90%", "95%", "98%", "99%",
                      "99.9%", "99.99%", "100%"]
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        return path

    def test_file_not_exists(self):
        """文件不存在时应返回 None"""
        result = analyze_locust_stats("/nonexistent/path.csv")
        self.assertIsNone(result)

    def test_parse_valid_csv(self):
        """应正确解析有效的 stats CSV"""
        path = self._create_stats_csv([
            {"Type": "POST", "Name": "/api/auth/login", "Request Count": "100",
             "Failure Count": "10", "Median Response Time": "5000",
             "Average Response Time": "5500", "Min Response Time": "100",
             "Max Response Time": "30000", "Average Content Size": "200",
             "Requests/s": "1.5", "Failures/s": "0.15",
             "50%": "5000", "66%": "6000", "75%": "7000", "80%": "8000",
             "90%": "9000", "95%": "10000", "98%": "12000", "99%": "15000",
             "99.9%": "20000", "99.99%": "25000", "100%": "30000"},
        ])
        result = analyze_locust_stats(path)
        self.assertIsNotNone(result)
        self.assertIn("/api/auth/login", result)
        self.assertEqual(result["/api/auth/login"]["requests"], 100)
        self.assertEqual(result["/api/auth/login"]["failures"], 10)

    def test_skip_aggregated(self):
        """应跳过 Aggregated 行"""
        path = self._create_stats_csv([
            {"Type": "", "Name": "Aggregated", "Request Count": "100",
             "Failure Count": "10", "Median Response Time": "5000",
             "Average Response Time": "5500", "Min Response Time": "100",
             "Max Response Time": "30000", "Average Content Size": "200",
             "Requests/s": "1.5", "Failures/s": "0.15",
             "50%": "5000", "66%": "6000", "75%": "7000", "80%": "8000",
             "90%": "9000", "95%": "10000", "98%": "12000", "99%": "15000",
             "99.9%": "20000", "99.99%": "25000", "100%": "30000"},
        ])
        result = analyze_locust_stats(path)
        self.assertIsNotNone(result)
        self.assertNotIn("Aggregated", result)


class TestAnalyzeMonitorData(unittest.TestCase):
    """analyze.py - analyze_monitor_data 测试"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def _create_monitor_csv(self, rows):
        path = os.path.join(self.temp_dir, "test_monitor.csv")
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'cpu_percent', 'memory_mb', 'connections'])
            for row in rows:
                writer.writerow(row)
        return path

    def test_file_not_exists(self):
        """文件不存在时应返回 None"""
        result = analyze_monitor_data("/nonexistent/monitor.csv")
        self.assertIsNone(result)

    def test_parse_valid_csv(self):
        """应正确解析有效的 monitor CSV"""
        path = self._create_monitor_csv([
            [0, 10.5, 200, 5],
            [1, 20.3, 205, 8],
            [2, 15.0, 210, 6],
        ])
        result = analyze_monitor_data(path)
        self.assertIsNotNone(result)
        timestamps, cpu, mem, conns, stats = result
        self.assertEqual(len(timestamps), 3)
        self.assertAlmostEqual(stats['cpu_avg'], (10.5 + 20.3 + 15.0) / 3, places=1)
        self.assertEqual(stats['mem_max'], 210)
        self.assertEqual(stats['conn_max'], 8)

    def test_empty_csv(self):
        """空数据应返回 None"""
        path = self._create_monitor_csv([])
        result = analyze_monitor_data(path)
        self.assertIsNone(result)

    def test_mem_growth_calculation(self):
        """内存增长应正确计算"""
        path = self._create_monitor_csv([
            [0, 10, 200, 5],
            [1, 20, 350, 10],
        ])
        result = analyze_monitor_data(path)
        self.assertIsNotNone(result)
        _, _, _, _, stats = result
        self.assertEqual(stats['mem_growth'], 150)


if __name__ == "__main__":
    unittest.main()
