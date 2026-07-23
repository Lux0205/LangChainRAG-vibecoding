"""
服务端资源监控
实时采集后端进程的 CPU、内存、连接数
"""
import sys
import os
import time
import csv
import psutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import RESULTS_DIR


def find_uvicorn_process():
    """查找 uvicorn 进程"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'uvicorn' in cmdline and 'app.main' in cmdline:
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def monitor_server(pid=None, duration=70, output_file=None):
    """
    监控服务端资源

    Args:
        pid: 进程PID，None则自动查找uvicorn
        duration: 监控时长（秒）
        output_file: 输出CSV文件路径
    """
    if pid is None:
        proc = find_uvicorn_process()
        if proc is None:
            print("❌ 未找到 uvicorn 进程，请先启动后端服务")
            return False
        pid = proc.pid
    else:
        try:
            proc = psutil.Process(pid)
        except psutil.NoSuchProcess:
            print(f"❌ 进程 {pid} 不存在")
            return False

    if output_file is None:
        output_file = os.path.join(RESULTS_DIR, "monitor.csv")

    print(f"=" * 50)
    print(f"  📊 服务端资源监控")
    print(f"  PID: {pid}")
    print(f"  进程: {proc.name()}")
    print(f"  时长: {duration}秒")
    print(f"  输出: {output_file}")
    print(f"=" * 50)

    # 获取初始状态
    proc.cpu_percent()  # 第一次调用返回0，需要预热

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'cpu_percent', 'memory_mb', 'memory_percent',
                         'connections', 'threads', 'open_files'])

        start_time = time.time()
        sample_count = 0

        try:
            while time.time() - start_time < duration:
                try:
                    cpu = proc.cpu_percent()
                    mem_info = proc.memory_info()
                    mem_mb = mem_info.rss / 1024 / 1024
                    mem_percent = proc.memory_percent()
                    connections = len(proc.connections())
                    threads = proc.num_threads()
                    open_files = len(proc.open_files())

                    elapsed = time.time() - start_time
                    writer.writerow([
                        f"{elapsed:.1f}",
                        f"{cpu:.1f}",
                        f"{mem_mb:.1f}",
                        f"{mem_percent:.1f}",
                        connections,
                        threads,
                        open_files
                    ])

                    sample_count += 1

                    # 每10秒打印一次摘要
                    if sample_count % 10 == 0:
                        print(f"  [{elapsed:.0f}s] CPU:{cpu:.1f}% MEM:{mem_mb:.0f}MB "
                              f"CONN:{connections} THR:{threads}")

                    time.sleep(1)

                except psutil.NoSuchProcess:
                    print(f"❌ 进程 {pid} 已退出")
                    break
                except Exception as e:
                    print(f"  [警告] 采样异常: {e}")
                    time.sleep(1)

        except KeyboardInterrupt:
            print(f"\n监控被用户中断")

    print(f"\n监控完成，共 {sample_count} 个采样点")
    print(f"数据已保存: {output_file}")

    # 输出统计摘要
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if rows:
                cpu_values = [float(r['cpu_percent']) for r in rows if float(r['cpu_percent']) > 0]
                mem_values = [float(r['memory_mb']) for r in rows]
                conn_values = [int(r['connections']) for r in rows]

                if cpu_values:
                    print(f"\n📈 统计摘要:")
                    print(f"  CPU  - 平均: {sum(cpu_values)/len(cpu_values):.1f}%, "
                          f"最高: {max(cpu_values):.1f}%")
                if mem_values:
                    print(f"  内存 - 起始: {mem_values[0]:.0f}MB, "
                          f"结束: {mem_values[-1]:.0f}MB, "
                          f"峰值: {max(mem_values):.0f}MB")
                if conn_values:
                    print(f"  连接 - 平均: {sum(conn_values)/len(conn_values):.0f}, "
                          f"峰值: {max(conn_values)}")

    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="监控服务端资源")
    parser.add_argument("--pid", type=int, default=None, help="进程PID（默认自动查找uvicorn）")
    parser.add_argument("-d", "--duration", type=int, default=70, help="监控时长秒数（默认70）")
    parser.add_argument("-o", "--output", type=str, default=None, help="输出CSV路径")
    args = parser.parse_args()
    monitor_server(args.pid, args.duration, args.output)
