"""
最小可运行的 Flask 模拟服务。

用途：
1. 作为被监控对象，暴露 /health、/predict、/metrics
2. 通过 src.instrumentation 中间件自动产生日志与指标
3. 支持按 customer_tier 记录业务指标
"""

from __future__ import annotations

import random
import sys
import time
from pathlib import Path

from flask import Flask, jsonify, request


# 让脚本支持从项目根目录外启动时也能导入 src 包
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.instrumentation import (  # noqa: E402
    MetricsMiddleware,
    business_predictions_total,
    metrics_endpoint,
)


app = Flask(__name__)
metrics = MetricsMiddleware(app)


@app.route("/health", methods=["GET"])
def health():
    """健康检查端点：用于存活探测与基础请求计数。"""
    return jsonify({"status": "ok"})


@app.route("/predict", methods=["POST"])
def predict():
    """
    模拟预测端点：
    - 接收 customer_tier（免费/付费分层）
    - 模拟推理耗时
    - 上报模型指标与业务指标
    """
    payload = request.get_json(silent=True) or {}
    customer_tier = payload.get("customer_tier", "free")
    if customer_tier not in {"free", "standard", "premium", "enterprise"}:
        customer_tier = "free"

    # 模拟推理延迟：20ms 到 250ms
    inference_time = random.uniform(0.02, 0.25)
    time.sleep(inference_time)

    prediction_class = random.choice(["cat", "dog", "bird"])
    confidence = round(random.uniform(0.7, 0.99), 4)

    metrics.track_prediction(
        model_name="resnet50",
        prediction_class=prediction_class,
        confidence=confidence,
        inference_time=inference_time,
    )

    # 仅对付费用户计数，体现“业务价值指标”
    if customer_tier != "free":
        business_predictions_total.labels(customer_tier=customer_tier).inc()

    return jsonify(
        {
            "prediction": prediction_class,
            "confidence": confidence,
            "customer_tier": customer_tier,
        }
    )


@app.route("/error", methods=["GET"])
def force_error():
    """故障注入端点：用于模拟 5xx，验证错误率告警。"""
    return jsonify({"error": "simulated failure"}), 500


@app.route("/slow", methods=["GET"])
def slow_response():
    """慢请求端点：用于拉高 P95/P99 延迟。"""
    time.sleep(1.2)
    return jsonify({"status": "slow-ok"})


@app.route("/metrics", methods=["GET"])
def metrics_view():
    """Prometheus 抓取端点。"""
    return metrics_endpoint()


if __name__ == "__main__":
    # 容器内监听 5000；k3s 通过 Service/NodePort 暴露到宿主机
    app.run(host="0.0.0.0", port=5000)
