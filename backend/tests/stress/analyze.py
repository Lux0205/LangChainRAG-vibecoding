"""
压力测试结果分析 + 生成图表报告
"""
import sys
import os
import csv
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use('Agg')  # 无GUI环境
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

from config import RESULTS_DIR, REPORTS_DIR


# 设置中文字体
def setup_chinese_font():
    """尝试设置中文字体"""
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simhei.ttf",     # 黑体
        "C:/Windows/Fonts/simsun.ttc",     # 宋体
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            fm.fontManager.addfont(fp)
            plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun']
            plt.rcParams['axes.unicode_minus'] = False
            return True
    return False


def analyze_locust_stats(stats_csv):
    """分析 Locust 统计数据"""
    if not os.path.exists(stats_csv):
        print(f"❌ 未找到统计文件: {stats_csv}")
        return None

    print(f"\n{'=' * 60}")
    print(f"  📊 Locust 压测结果分析")
    print(f"{'=' * 60}")

    # 读取统计数据
    endpoints = {}
    with open(stats_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Name", "unknown")
            if name == "Aggregated" or not name.strip():
                continue

            endpoints[name] = {
                "requests": int(row.get("Request Count", 0)),
                "failures": int(row.get("Failure Count", 0)),
                "avg_rt": float(row.get("Average Response Time", 0)),
                "min_rt": float(row.get("Min Response Time", 0)),
                "max_rt": float(row.get("Max Response Time", 0)),
                "p50": float(row.get("50%", 0)),
                "p95": float(row.get("95%", 0)),
                "p99": float(row.get("99%", 0)),
                "rps": float(row.get("Requests/s", 0)),
            }

    # 打印各接口统计
    print(f"\n{'接口':<40} {'请求':>6} {'失败':>6} {'P50':>8} {'P95':>8} {'P99':>8} {'RPS':>6}")
    print("-" * 90)

    for name, data in endpoints.items():
        fail_rate = data["failures"] / data["requests"] * 100 if data["requests"] > 0 else 0
        print(f"{name:<40} {data['requests']:>6} {data['failures']:>6} "
              f"{data['p50']:>7.0f}ms {data['p95']:>7.0f}ms {data['p99']:>7.0f}ms "
              f"{data['rps']:>5.1f}")
        if fail_rate > 0:
            print(f"  └─ 错误率: {fail_rate:.1f}%")

    return endpoints


def analyze_monitor_data(monitor_csv):
    """分析监控数据"""
    if not os.path.exists(monitor_csv):
        print(f"❌ 未找到监控文件: {monitor_csv}")
        return None

    print(f"\n{'=' * 60}")
    print(f"  🖥️ 服务端资源监控分析")
    print(f"{'=' * 60}")

    timestamps, cpu, mem, conns = [], [], [], []
    with open(monitor_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamps.append(float(row['timestamp']))
            cpu.append(float(row['cpu_percent']))
            mem.append(float(row['memory_mb']))
            conns.append(int(row['connections']))

    if not timestamps:
        print("无数据")
        return None

    # 过滤掉0值（CPU首次采样为0）
    cpu_non_zero = [c for c in cpu if c > 0] or [0]

    stats = {
        "duration": timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 0,
        "cpu_avg": sum(cpu_non_zero) / len(cpu_non_zero),
        "cpu_max": max(cpu),
        "mem_start": mem[0] if mem else 0,
        "mem_end": mem[-1] if mem else 0,
        "mem_max": max(mem) if mem else 0,
        "mem_growth": (mem[-1] - mem[0]) if mem else 0,
        "conn_avg": sum(conns) / len(conns) if conns else 0,
        "conn_max": max(conns) if conns else 0,
    }

    print(f"\n  监控时长: {stats['duration']:.0f}秒")
    print(f"  CPU  - 平均: {stats['cpu_avg']:.1f}%, 峰值: {stats['cpu_max']:.1f}%")
    print(f"  内存 - 起始: {stats['mem_start']:.0f}MB, 结束: {stats['mem_end']:.0f}MB, "
          f"峰值: {stats['mem_max']:.0f}MB")
    print(f"  内存增长: {stats['mem_growth']:.0f}MB "
          f"({'⚠️ 可能存在泄漏' if stats['mem_growth'] > 100 else '✅ 正常'})")
    print(f"  连接 - 平均: {stats['conn_avg']:.0f}, 峰值: {stats['conn_max']}")

    return timestamps, cpu, mem, conns, stats


def generate_charts(monitor_data, output_dir=REPORTS_DIR):
    """生成图表"""
    if monitor_data is None:
        return

    timestamps, cpu, mem, conns, stats = monitor_data

    setup_chinese_font()

    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    fig.suptitle("压力测试 - 服务端资源监控", fontsize=16, fontweight='bold')

    # CPU 曲线
    axes[0].plot(timestamps, cpu, color='#2196F3', linewidth=1.5)
    axes[0].set_ylabel("CPU 使用率 (%)")
    axes[0].set_title(f"CPU (平均: {stats['cpu_avg']:.1f}%, 峰值: {stats['cpu_max']:.1f}%)")
    axes[0].grid(True, alpha=0.3)
    axes[0].axhline(y=90, color='red', linestyle='--', alpha=0.5, label='90% 警戒线')
    axes[0].legend()

    # 内存曲线
    axes[1].plot(timestamps, mem, color='#4CAF50', linewidth=1.5)
    axes[1].set_ylabel("内存 (MB)")
    axes[1].set_title(f"内存 (起始: {stats['mem_start']:.0f}MB → 结束: {stats['mem_end']:.0f}MB)")
    axes[1].grid(True, alpha=0.3)

    # 连接数曲线
    axes[2].plot(timestamps, conns, color='#FF9800', linewidth=1.5)
    axes[2].set_ylabel("连接数")
    axes[2].set_xlabel("时间 (秒)")
    axes[2].set_title(f"网络连接 (平均: {stats['conn_avg']:.0f}, 峰值: {stats['conn_max']})")
    axes[2].grid(True, alpha=0.3)
    axes[2].axhline(y=50, color='red', linestyle='--', alpha=0.5, label='连接池上限(50)')
    axes[2].legend()

    plt.tight_layout()
    chart_path = os.path.join(output_dir, "monitor_chart.png")
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\n✅ 图表已保存: {chart_path}")


def generate_summary_report(locust_stats, monitor_stats, output_dir=REPORTS_DIR):
    """生成文字摘要报告"""
    report_path = os.path.join(output_dir, "summary_report.txt")

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("  压力测试报告\n")
        f.write("=" * 60 + "\n\n")

        if locust_stats:
            f.write("【接口性能】\n")
            f.write(f"{'接口':<40} {'请求':>6} {'失败':>6} {'P50':>8} {'P95':>8} {'P99':>8} {'RPS':>6}\n")
            f.write("-" * 90 + "\n")
            for name, data in locust_stats.items():
                f.write(f"{name:<40} {data['requests']:>6} {data['failures']:>6} "
                        f"{data['p50']:>7.0f}ms {data['p95']:>7.0f}ms {data['p99']:>7.0f}ms "
                        f"{data['rps']:>5.1f}\n")

        if monitor_stats:
            f.write("\n【服务端资源】\n")
            f.write(f"  CPU  - 平均: {monitor_stats['cpu_avg']:.1f}%, 峰值: {monitor_stats['cpu_max']:.1f}%\n")
            f.write(f"  内存 - 起始: {monitor_stats['mem_start']:.0f}MB, "
                    f"结束: {monitor_stats['mem_end']:.0f}MB, 峰值: {monitor_stats['mem_max']:.0f}MB\n")
            f.write(f"  连接 - 平均: {monitor_stats['conn_avg']:.0f}, 峰值: {monitor_stats['conn_max']}\n")

    print(f"✅ 报告已保存: {report_path}")


def main():
    """主函数：分析所有结果"""
    setup_chinese_font()

    # 查找 Locust 统计文件
    stats_files = glob.glob(os.path.join(RESULTS_DIR, "*_stats.csv"))
    if not stats_files:
        # 也检查当前目录
        stats_files = glob.glob("*_stats.csv")

    locust_stats = None
    if stats_files:
        # 使用最新的
        latest = max(stats_files, key=os.path.getmtime)
        locust_stats = analyze_locust_stats(latest)

    # 查找监控文件
    monitor_csv = os.path.join(RESULTS_DIR, "monitor.csv")
    monitor_data = analyze_monitor_data(monitor_csv)

    # 生成图表
    if monitor_data:
        generate_charts(monitor_data)

    # 生成摘要报告
    monitor_stats = monitor_data[-1] if monitor_data else None
    generate_summary_report(locust_stats, monitor_stats)

    print(f"\n{'=' * 60}")
    print(f"  分析完成！")
    print(f"  结果目录: {RESULTS_DIR}")
    print(f"  报告目录: {REPORTS_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
