"""
ML API 的 Prometheus 指标埋点

本模块为 ML 推理 API 提供完整的指标埋点能力，
包括应用指标、基础设施指标以及 ML 专属指标。

学习目标：
- 理解 Prometheus 指标类型（Counter、Gauge、Histogram、Summary）
- 学习如何为 Web 应用做指标埋点
- 实现自动化请求跟踪中间件
- 以 Prometheus 格式导出指标
- 跟踪 ML 专属指标（预测、延迟、置信度）

参考资料：
- Prometheus Python Client: https://github.com/prometheus/client_python
- Prometheus Best Practices: https://prometheus.io/docs/practices/naming/
"""

from prometheus_client import Counter, Histogram, Gauge, Info, Summary
from prometheus_client import CollectorRegistry, generate_latest
from flask import Flask, Response, request, g
import time
import logging
from typing import Dict, Optional, Callable
import functools

# TODO: 导入 psutil 以采集系统指标（CPU、内存、磁盘）
# 提示：pip install psutil
# import psutil

logger = logging.getLogger(__name__)


# =============================================================================
# 指标注册表
# =============================================================================

# TODO: 为所有指标创建自定义 registry
# 提示：registry = CollectorRegistry()
# 为什么要用自定义 registry？可以更精细地控制暴露哪些指标，
# 对测试和多应用部署都更友好

registry = CollectorRegistry()

# =============================================================================
# 应用信息指标
# =============================================================================

# TODO: 为应用元信息创建 Info 指标
# 用于提供应用静态信息
#
# 示例：
app_info = Info(
    'app_info',
    'Application information',
    registry=registry
)
#
# 然后写入信息：
app_info.info({
    'version': '1.0.0',
    'environment': 'production',
    'service': 'ml-api',
    'model_version': 'resnet50-v1'
})


# =============================================================================
# HTTP 请求指标
# =============================================================================

# TODO: 创建 HTTP 请求总量 Counter
# Counter：只增不减（不会下降或重置）
# 适用于：总请求数、总错误数、总预测数
#
# 语法：
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],  # 维度标签
    registry=registry
)
#
# 标签使用最佳实践：
# - 标签用于表达维度（method、endpoint、status）
# - 保持低基数（避免把 user_id、request_id 当标签）
# - 各指标尽量使用一致标签名


# TODO: 创建 HTTP 请求耗时 Histogram
# Histogram：对观测值采样并按 bucket 计数
# 适用于：请求时长、响应大小、推理延迟
#
# 语法：
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=registry
)
#
# 桶配置建议：
# - 先按 2 或 10 的幂次递增设计
# - 覆盖预期范围（API 请求通常 0.01s 到 10s）
# - 在关键阈值（如 SLA 边界）放置额外桶
# - 桶太多会导致高基数，太少会导致分位数不精确


# TODO: 创建 HTTP 请求大小 Histogram（字节）
# 跟踪入站请求体大小
# 适用于：识别大 payload、优化数据传输
#
# 桶建议：[100, 1000, 10000, 100000, 1000000, 10000000]

# TODO: 创建 HTTP 响应大小 Histogram（字节）
# 跟踪出站响应体大小
http_request_size_bytes = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
    buckets=[100, 1000, 10000, 100000, 1000000, 10000000],
    registry=registry
)

# TODO: 创建正在处理中的 HTTP 请求计数器
# 实际应使用 Gauge，因为它会增减
http_requests_in_flight = Gauge(
    'http_requests_in_flight',
    'Current number of HTTP requests being processed',
    registry=registry
)


# =============================================================================
# ML 模型指标
# =============================================================================

# TODO: 创建模型预测总量 Counter
# 按模型名和预测类别统计
#
model_predictions_total = Counter(
    'model_predictions_total',
    'Total number of model predictions',
    ['model_name', 'prediction_class'],
    registry=registry
)


# TODO: 创建模型推理耗时 Histogram
# 这是 ML 系统关键指标：推理耗时多少？
#
# 推理桶建议：[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
# （1ms 到 1s 范围）

model_inference_duration_seconds = Histogram(
    'model_inference_duration_seconds',
    'Model inference duration in seconds',
    ['model_name'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=registry
)


# TODO: 创建模型预测置信度 Histogram
# 跟踪置信度分布
# 有助于识别模型不确定场景
#
# 桶建议：[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0]


model_prediction_confidence = Histogram(
    'model_prediction_confidence',
    'Model prediction confidence',
    ['model_name'],
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0],
    registry=registry
)


# TODO: 创建当前模型准确率 Gauge
# 通过真实标签反馈周期性更新（如每天）
#
model_accuracy = Gauge(
    'model_accuracy',
    'Current model accuracy (0-1)',
    ['model_name'],
    registry=registry
)


# TODO: 创建模型预测错误 Counter
# 跟踪预测失败（异常、超时等）

model_prediction_errors_total = Counter(
    'model_prediction_errors_total',
    'Total number of model prediction errors',
    ['model_name', 'error_type'],
    registry=registry
)


# =============================================================================
# 数据质量指标
# =============================================================================

# TODO: 创建数据漂移分数 Gauge
# 用于衡量输入数据分布偏移
#
data_drift_score = Gauge(
    'data_drift_score',
    'Data drift score (0-1, higher = more drift)',
    ['feature_name'],
    registry=registry
)


# TODO: 创建请求缺失特征 Counter
# 跟踪数据质量问题
#
missing_features_total = Counter(
    'missing_features_total',
    'Total requests with missing features',
    ['feature_name'],
    registry=registry
)


# TODO: 创建无效请求 Counter
# 跟踪请求格式错误、Schema 违规等

invalid_requests_total = Counter(
    'invalid_requests_total',
    'Total number of invalid requests',
    ['request_type'],
    registry=registry
)

# =============================================================================
# 基础设施指标
# =============================================================================

# TODO: 创建内存使用量 Gauge（字节）
# 使用 psutil 获取当前内存使用
#
memory_usage_bytes = Gauge(
    'process_memory_usage_bytes',
    'Current memory usage in bytes',
    registry=registry
)


# TODO: 创建 CPU 使用率 Gauge（百分比）
cpu_usage_percent = Gauge(
    'process_cpu_usage_percent',
    'Current CPU usage percentage',
    registry=registry
)


# TODO: 创建活跃数据库连接数 Gauge（如果使用数据库）

active_database_connections = Gauge(
    'active_database_connections',
    'Current number of active database connections',
    registry=registry
)

# 磁盘读写指标
disk_read_bytes_total = Gauge(
    'disk_read_bytes_total',
    'Total number of bytes read from disk',
    registry=registry
)
disk_write_bytes_total = Gauge(
    'disk_write_bytes_total',
    'Total number of bytes written to disk',
    registry=registry
)

# 网络读写指标
network_receive_bytes_total = Gauge(
    'network_receive_bytes_total',
    'Total number of bytes received from network',
    registry=registry
)
network_transmit_bytes_total = Gauge(
    'network_transmit_bytes_total',
    'Total number of bytes transmitted to network',
    registry=registry
)

# =============================================================================
# 业务指标
# =============================================================================

# TODO: 创建与收入相关的预测 Counter
# 如果你的 ML 系统有业务价值，建议跟踪！
#
# 示例：
business_predictions_total = Counter(
    'business_predictions_total',
    'Total predictions for paying customers',
    ['customer_tier'],
    registry=registry
)


# =============================================================================
# Flask 指标中间件
# =============================================================================

class MetricsMiddleware:
    """
    自动跟踪 HTTP 请求指标的 Flask 中间件。

    该中间件会：
    1. 对所有端点跟踪请求次数、时长、大小
    2. 记录响应状态码
    3. 优雅处理异常场景
    4. 提供 ML 专属指标跟踪辅助方法

    用法：
        app = Flask(__name__)
        metrics = MetricsMiddleware(app)

        @app.route('/predict', methods=['POST'])
        def predict():
            # 你的预测代码
            result = model.predict(data)

            # 跟踪预测指标
            metrics.track_prediction(
                model_name='resnet50',
                prediction_class='cat',
                confidence=0.95,
                inference_time=0.045
            )

            return jsonify({'prediction': result})
    """

    def __init__(self, app: Flask):
        """
        初始化指标中间件。

        Args:
            app: Flask 应用实例
        """
        self.app = app
        self.setup_middleware()

    def setup_middleware(self):
        """设置请求前后处理器。"""

        # TODO: 实现 before_request 处理器
        # 每次请求前执行
        #
        # 任务：
        # 1. 记录开始时间：g.start_time = time.time()
        # 2. 增加 in-flight 请求 Gauge
        # 3. 记录请求大小
        #
        # 提示：使用 @self.app.before_request 装饰器
        @self.app.before_request
        def before_request():
            g.start_time = time.time()
            http_requests_in_flight.inc()
            # 获取请求大小
            request_size = len(request.get_data())
            http_request_size_bytes.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown'
            ).observe(request_size)


        # TODO: 实现 after_request 处理器
        # 每次请求后执行（即使请求失败）
        #
        # 任务：
        # 1. 计算请求耗时
        # 2. 在 Histogram 中记录耗时
        # 3. 按状态码递增请求 Counter
        # 4. 记录响应大小
        # 5. 减少 in-flight 请求 Gauge
        #
        # 提示：使用 @self.app.after_request 装饰器
        @self.app.after_request
        def after_request(response):
            # 计算耗时
            if hasattr(g, 'start_time'):
                duration = time.time() - g.start_time
        
                # 记录耗时
                http_request_duration_seconds.labels(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown'
                ).observe(duration)
        
                # 按状态码记录请求次数
                http_requests_total.labels(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown',
                    status=response.status_code
                ).inc()
        
                # 减少 in-flight
                http_requests_in_flight.dec()
        
            return response


        # TODO: 为异常场景实现 teardown_request 处理器
        # 即使请求抛异常也会执行
        # 用于确保 in-flight Gauge 总能回落
        #
        @self.app.teardown_request
        def teardown_request(exception=None):
            if exception:
                http_requests_in_flight.dec()

    def track_prediction(
        self,
        model_name: str,
        prediction_class: str,
        confidence: float,
        inference_time: float
    ):
        """
        跟踪 ML 预测指标。

        Args:
            model_name: 模型名称（例如 'resnet50'）
            prediction_class: 预测类别（例如 'cat'、'dog'）
            confidence: 预测置信度（0-1）
            inference_time: 推理耗时（秒）
        """
        # TODO: 实现预测指标跟踪
        # 1. 增加预测计数器
        # 2. 记录推理耗时
        # 3. 记录置信度
        #
        # 示例：
        model_predictions_total.labels(
            model_name=model_name,
            prediction_class=prediction_class
        ).inc()
        
        model_inference_duration_seconds.labels(
            model_name=model_name
        ).observe(inference_time)
        
        model_prediction_confidence.labels(
            model_name=model_name
        ).observe(confidence)


    def track_data_quality(
        self,
        missing_features: Dict[str, int],
        drift_scores: Optional[Dict[str, float]] = None
    ):
        """
        跟踪数据质量指标。

        Args:
            missing_features: 缺失特征计数字典 {feature_name: count}
            drift_scores: 漂移分数字典 {feature_name: drift_score}
        """
        # TODO: 实现数据质量跟踪
        # 1. 更新缺失特征 Counter
        # 2. 更新漂移分数 Gauge（如有）
        #
        for feature_name, count in missing_features.items():
            missing_features_total.labels(
                feature_name=feature_name
            ).inc(count)
        
        if drift_scores:
            for feature_name, score in drift_scores.items():
                data_drift_score.labels(
                    feature_name=feature_name
                ).set(score)


    def update_model_accuracy(self, model_name: str, accuracy: float):
        """
        更新模型准确率 Gauge。

        Args:
            model_name: 模型名称
            accuracy: 当前准确率（0-1）
        """
        # TODO: 更新模型准确率 Gauge
        model_accuracy.labels(model_name=model_name).set(accuracy)


# =============================================================================
# 系统指标采集器
# =============================================================================

class SystemMetricsCollector:
    """
    使用 psutil 采集系统级指标。

    建议在后台线程周期性运行，用于持续更新系统指标。
    """

    def __init__(self, interval: int = 15):
        """
        初始化系统指标采集器。

        Args:
            interval: 采集间隔（秒）
        """
        self.interval = interval

    def collect_once(self):
        """采集一次系统指标。"""
        # TODO: 采集并更新系统指标
        #
        # 1. 内存使用：
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_usage_bytes.set(memory_info.rss)
        #
        # 2. CPU 使用率：
        cpu_percent = process.cpu_percent(interval=1)
        cpu_usage_percent.set(cpu_percent)
        #
        # 3. （可选）磁盘 I/O、网络 I/O 等
        disk_io_counters = psutil.disk_io_counters()
        disk_read_bytes_total.set(disk_io_counters.read_bytes)
        disk_write_bytes_total.set(disk_io_counters.write_bytes)

        network_io_counters = psutil.net_io_counters()
        network_receive_bytes_total.set(network_io_counters.bytes_recv)
        network_transmit_bytes_total.set(network_io_counters.bytes_sent)
    def start_background_collection(self):
        """在后台线程中启动指标采集。"""
        # TODO: 实现后台采集
        #
        # 提示：使用 threading.Thread 并设置 daemon=True
        #
        import threading
        
        def _collect_loop():
            while True:
                try:
                    self.collect_once()
                except Exception as e:
                    logger.error(f"采集系统指标失败：{e}")
                time.sleep(self.interval)
        
        thread = threading.Thread(target=_collect_loop, daemon=True)
        thread.start()
        logger.info(f"已启动系统指标采集（interval={self.interval}s）")



# =============================================================================
# 指标端点
# =============================================================================

def metrics_endpoint() -> Response:
    """
    以 Prometheus 格式暴露指标。

    Prometheus 通过抓取该端点来采集指标。

    Returns:
        Flask Response，内容为 Prometheus 文本格式指标
    """
    # TODO: 生成并返回指标
    #
    # 使用 prometheus_client.generate_latest() 导出全部指标，
    # 输出为 Prometheus 文本格式
    #
    return Response(
        generate_latest(registry),
        mimetype='text/plain; version=0.0.4; charset=utf-8'
    )

# =============================================================================
# 函数耗时装饰器
# =============================================================================

def timed(metric_name: str = None, labels: Dict[str, str] = None):
    """
    装饰器：统计函数执行时间并写入指标。

    用法：
        @timed(metric_name='function_duration_seconds', labels={'function': 'load_model'})
        def load_model():
            # 模型加载代码
            pass

    Args:
        metric_name: 用于记录耗时的 histogram 指标名
        labels: 要附加到指标上的标签
    """
    # TODO: 实现耗时装饰器
    #
    # 这是一个用于追踪任意函数耗时的进阶模式
    #
    # 提示：使用 functools.wraps 保留原函数元信息
    #
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                # 在指标中记录耗时
                # 你需要先创建/获取对应指标
                logger.debug(f"{func.__name__} 耗时 {duration:.4f}s")
        return wrapper
    return decorator


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    # TODO: 创建一个带指标的 Flask 示例应用
    #
    from flask import Flask, jsonify
    
    app = Flask(__name__)
    metrics = MetricsMiddleware(app)
    
    @app.route('/metrics')
    def metrics():
        return metrics_endpoint()
    
    @app.route('/predict', methods=['POST'])
    def predict():
        # 模拟预测
        import random
        time.sleep(random.uniform(0.01, 0.1))  # 模拟推理耗时
    
        prediction_class = random.choice(['cat', 'dog', 'bird'])
        confidence = random.uniform(0.7, 0.99)
        inference_time = random.uniform(0.01, 0.1)
    
        metrics.track_prediction(
            model_name='resnet50',
            prediction_class=prediction_class,
            confidence=confidence,
            inference_time=inference_time
        )
    
        return jsonify({
            'prediction': prediction_class,
            'confidence': confidence
        })
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'})
    
    # 启动系统指标采集
    collector = SystemMetricsCollector(interval=15)
    collector.start_background_collection()
    
    # 运行应用
    app.run(host='0.0.0.0', port=5000)

    print("请先实现上方示例 Flask 应用再测试指标！")
    print("\n测试步骤：")
    print("1. 实现本文件中的所有 TODO")
    print("2. 运行文件：python instrumentation.py")
    print("3. 发送请求：curl -X POST http://localhost:30500/predict（k8s NodePort）")
    print("4. 查看指标：curl http://localhost:30500/metrics")
    print("5. 在输出中确认你的自定义指标已出现！")
