"""
生产流量模拟脚本。

功能：
1. 按固定 QPS 持续向 Flask 服务发送请求
2. 混合健康检查、预测、慢请求、故障请求
3. 支持控制持续时长、错误流量比例、慢请求比例
"""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class TrafficStats:
    """运行统计信息，便于观察模拟效果。"""

    total: int = 0
    success: int = 0
    # 非预期的失败（连接失败、非 /error 的 5xx 等）
    unexpected_failures: int = 0
    predict_calls: int = 0
    health_calls: int = 0
    slow_calls: int = 0
    # 访问 /error 且收到预期 5xx 的次数（用于告警演练，不算失败）
    error_injection_ok: int = 0


def send_get(url: str, timeout: float) -> int:
    """发送 GET 请求并返回状态码。"""
    req = urllib.request.Request(url=url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status


def send_predict(url: str, timeout: float) -> int:
    """发送预测请求，并随机选择客户等级。"""
    customer_tier = random.choices(
        population=["free", "standard", "premium", "enterprise"],
        weights=[70, 20, 8, 2],
        k=1,
    )[0]
    payload = {
        "features": [random.random(), random.random(), random.random()],
        "customer_tier": customer_tier,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status


def run_simulation(
    base_url: str,
    qps: float,
    duration_seconds: int,
    error_ratio: float,
    slow_ratio: float,
    timeout: float,
    verbose: bool,
):
    """按给定参数执行流量模拟主循环。"""
    stats = TrafficStats()
    interval = 1.0 / qps
    end_time = time.time() + duration_seconds

    while time.time() < end_time:
        loop_start = time.time()
        r = random.random()

        if r < error_ratio:
            endpoint = "/error"
            request_type = "error"
        elif r < error_ratio + slow_ratio:
            endpoint = "/slow"
            request_type = "slow"
        elif r < 0.85:
            endpoint = "/predict"
            request_type = "predict"
        else:
            endpoint = "/health"
            request_type = "health"

        full_url = f"{base_url}{endpoint}"
        stats.total += 1

        try:
            if request_type == "predict":
                status = send_predict(full_url, timeout)
                stats.predict_calls += 1
            else:
                status = send_get(full_url, timeout)
                if request_type == "health":
                    stats.health_calls += 1
                elif request_type == "slow":
                    stats.slow_calls += 1
                else:
                    stats.error_calls += 1

            if 200 <= status < 400:
                stats.success += 1
            else:
                stats.unexpected_failures += 1
                print(f"[非预期状态码] {endpoint} -> {status}")
        except urllib.error.HTTPError as e:
            # /error 端点故意返回 5xx：属于预期行为，urllib 仍会抛 HTTPError
            try:
                e.read()
            except Exception:
                pass
            if request_type == "error" and 500 <= e.code < 600:
                stats.error_injection_ok += 1
                if verbose:
                    print(f"[预期故障注入] {endpoint} -> {e.code}")
            else:
                stats.unexpected_failures += 1
                print(f"[HTTPError] {endpoint} -> {e.code}")
        except Exception as e:  # noqa: BLE001
            # 网络中断/连接拒绝等异常
            stats.unexpected_failures += 1
            print(f"[RequestFailed] {endpoint} -> {e}")

        # 固定节奏发流量，尽量贴近目标 QPS
        elapsed = time.time() - loop_start
        sleep_time = interval - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

    print("\n=== 流量模拟结束 ===")
    print(f"总请求数: {stats.total}")
    print(f"成功数(2xx/3xx): {stats.success}")
    print(f"预期故障注入(/error 返回 5xx): {stats.error_injection_ok}")
    print(f"意外失败数: {stats.unexpected_failures}")
    print(f"/predict: {stats.predict_calls}")
    print(f"/health:  {stats.health_calls}")
    print(f"/slow:    {stats.slow_calls}")


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="模拟生产流量")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:30500",
        help="目标服务地址（k8s Service NodePort，见 deployments/kustomize/ml-api.yaml）",
    )
    parser.add_argument("--qps", type=float, default=5.0, help="每秒请求数")
    parser.add_argument("--duration", type=int, default=120, help="持续时间（秒）")
    parser.add_argument("--error-ratio", type=float, default=0.1, help="错误请求比例（0-1）")
    parser.add_argument("--slow-ratio", type=float, default=0.1, help="慢请求比例（0-1）")
    parser.add_argument("--timeout", type=float, default=3.0, help="单次请求超时时间（秒）")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="打印每一次预期故障注入（默认安静，避免 /error 的 500 刷屏）",
    )
    args = parser.parse_args()

    if args.qps <= 0:
        parser.error("--qps 必须大于 0")
    if not (0 <= args.error_ratio <= 1):
        parser.error("--error-ratio 必须在 [0, 1] 区间")
    if not (0 <= args.slow_ratio <= 1):
        parser.error("--slow-ratio 必须在 [0, 1] 区间")
    if args.error_ratio + args.slow_ratio >= 1:
        parser.error("--error-ratio + --slow-ratio 必须小于 1")
    if args.duration <= 0:
        parser.error("--duration 必须大于 0")

    # 未显式传参时，自动从 k8s Service 读取 NodePort，避免端口动态分配后压测失败。
    if "--base-url" not in os.sys.argv:
        try:
            svc_port = subprocess.check_output(
                [
                    "kubectl",
                    "-n",
                    "monitoring-stack",
                    "get",
                    "svc",
                    "ml-api",
                    "-o",
                    "jsonpath={.spec.ports[0].nodePort}",
                ],
                text=True,
                timeout=3,
            ).strip()
            if svc_port:
                args.base_url = f"http://127.0.0.1:{svc_port}"
        except Exception:
            # 回退到默认端口，保持脚本在无 kubectl 环境可用。
            pass

    return args


if __name__ == "__main__":
    cli_args = parse_args()
    run_simulation(
        base_url=cli_args.base_url,
        qps=cli_args.qps,
        duration_seconds=cli_args.duration,
        error_ratio=cli_args.error_ratio,
        slow_ratio=cli_args.slow_ratio,
        timeout=cli_args.timeout,
        verbose=cli_args.verbose,
    )
