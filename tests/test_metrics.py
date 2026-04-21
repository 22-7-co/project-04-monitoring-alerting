"""
指标埋点单元测试

本文件包含用于验证指标是否正确埋点并以 Prometheus 格式导出的测试。

学习目标：
- 为 Prometheus 指标编写单元测试
- 测试指标递增与观测行为
- 验证指标导出格式
- 理解可观测性代码的测试策略

运行测试：
    pytest tests/test_metrics.py -v
    pytest tests/test_metrics.py::test_counter_increment -v

参考资料：
- pytest 文档：https://docs.pytest.org/
- prometheus_client 测试：https://github.com/prometheus/client_python
"""

import pytest
from prometheus_client import CollectorRegistry, Counter, Histogram, Gauge
from prometheus_client import generate_latest
import time
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def registry():
    """
    为每个测试创建独立的指标注册表。

    这样可确保测试彼此隔离，互不影响。
    """
    return CollectorRegistry()


@pytest.fixture
def sample_counter(registry):
    """创建用于测试的示例 Counter 指标。"""
    # TODO: 创建 Counter 指标
    return Counter(
        'test_requests_total',
        'Total test requests',
        ['method', 'endpoint'],
        registry=registry
    )


@pytest.fixture
def sample_histogram(registry):
    """创建用于测试的示例 Histogram 指标。"""
    # TODO: 创建 Histogram 指标
    return Histogram(
        'test_request_duration_seconds',
        'Test request duration',
        ['endpoint'],
        buckets=[0.1, 0.5, 1.0, 2.5, 5.0],
        registry=registry
    )


@pytest.fixture
def sample_gauge(registry):
    """创建用于测试的示例 Gauge 指标。"""
    # TODO: 创建 Gauge 指标
    return Gauge(
        'test_active_connections',
        'Test active connections',
        registry=registry
    )


# =============================================================================
# Counter Tests
# =============================================================================

def test_counter_increment(sample_counter):
    """测试 Counter 是否能正确递增。"""
    # TODO: 实现测试
    #
    # 步骤：
    # 1. 获取初始值（应为 0 或尚不存在）
    # 2. 递增 counter
    # 3. 断言值增加了 1
    #
    # 示例：
    # 递增 counter
    sample_counter.labels(method='GET', endpoint='/test').inc()
    
    # 获取 counter 值
    # 注意：测试中可通过 _value._value 访问 Counter 值
    value = sample_counter.labels(method='GET', endpoint='/test')._value._value
    
    assert value == 1.0



def test_counter_increment_by_amount(sample_counter):
    """测试 Counter 是否可以按指定数值递增。"""
    # TODO: 实现测试
    #
    sample_counter.labels(method='POST', endpoint='/predict').inc(5)
    value = sample_counter.labels(method='POST', endpoint='/predict')._value._value
    assert value == 5.0



def test_counter_multiple_labels(sample_counter):
    """测试 Counter 是否可独立跟踪不同标签组合。"""
    # TODO: 实现测试
    #
    # 递增不同标签组合
    sample_counter.labels(method='GET', endpoint='/health').inc()
    sample_counter.labels(method='POST', endpoint='/predict').inc(3)
    sample_counter.labels(method='GET', endpoint='/health').inc()
    #
    # 验证每个组合独立统计
    assert sample_counter.labels(method='GET', endpoint='/health')._value._value == 2.0
    assert sample_counter.labels(method='POST', endpoint='/predict')._value._value == 3.0




# =============================================================================
# Histogram Tests
# =============================================================================

def test_histogram_observe(sample_histogram):
    """测试 Histogram 是否能记录观测值。"""
    # TODO: 实现测试
    #
    # 记录若干观测值
    sample_histogram.labels(endpoint='/predict').observe(0.3)
    sample_histogram.labels(endpoint='/predict').observe(0.7)
    sample_histogram.labels(endpoint='/predict').observe(1.2)
    
    count = get_histogram_sample_value(
        sample_histogram,
        "count",
        endpoint="/predict"
    )
    assert count == 3.0

    total = get_histogram_sample_value(
        sample_histogram,
        "sum",
        endpoint="/predict"
    )
    assert total == pytest.approx(2.2)



def test_histogram_buckets(sample_histogram):
    """测试 Histogram 的 buckets 是否正确计数。"""
    # TODO: 实现测试
    #
    # 观测落入不同 bucket 的值
    sample_histogram.labels(endpoint='/test').observe(0.05)  # bucket: <= 0.1
    sample_histogram.labels(endpoint='/test').observe(0.3)   # bucket: <= 0.5
    sample_histogram.labels(endpoint='/test').observe(0.8)   # bucket: <= 1.0
    sample_histogram.labels(endpoint='/test').observe(3.0)   # bucket: <= 5.0
    
    assert get_histogram_sample_value(
        sample_histogram,
        "bucket",
        endpoint="/test",
        le="0.1"
    ) == 1.0
    assert get_histogram_sample_value(
        sample_histogram,
        "bucket",
        endpoint="/test",
        le="0.5"
    ) == 2.0
    assert get_histogram_sample_value(
        sample_histogram,
        "bucket",
        endpoint="/test",
        le="1.0"
    ) == 3.0
    assert get_histogram_sample_value(
        sample_histogram,
        "bucket",
        endpoint="/test",
        le="5.0"
    ) == 4.0



def test_histogram_time_decorator(sample_histogram):
    """测试 histogram.time() 装饰器是否可用。"""
    # TODO: 实现测试
    #
    # 将 histogram.time() 作为装饰器或上下文管理器使用
    with sample_histogram.labels(endpoint='/test').time():
        time.sleep(0.1)  # 模拟工作负载
    
    count = get_histogram_sample_value(
        sample_histogram,
        "count",
        endpoint="/test"
    )
    assert count == 1.0

    total = get_histogram_sample_value(
        sample_histogram,
        "sum",
        endpoint="/test"
    )
    assert total >= 0.1
    assert total < 0.2  # 允许少量额外开销


# =============================================================================
# Gauge Tests
# =============================================================================

def test_gauge_set(sample_gauge):
    """测试 Gauge 是否可设为指定值。"""
    # TODO: 实现测试
    #
    sample_gauge.set(42)
    assert sample_gauge._value._value == 42


def test_gauge_inc_dec(sample_gauge):
    """测试 Gauge 是否可以递增和递减。"""
    # TODO: 实现测试
    #
    # 初始为 0
    sample_gauge.set(0)
    #
    # 递增
    sample_gauge.inc()
    assert sample_gauge._value._value == 1
    #
    # 按指定值递增
    sample_gauge.inc(5)
    assert sample_gauge._value._value == 6
    #
    # 递减
    sample_gauge.dec(2)
    assert sample_gauge._value._value == 4



def test_gauge_set_to_current_time(sample_gauge):
    """测试 Gauge 是否可用于记录时间戳。"""
    # TODO: 实现测试
    #
    sample_gauge.set_to_current_time()
    current_time = time.time()
    #
    # # Gauge 值应接近当前时间
    assert sample_gauge._value._value == pytest.approx(current_time, abs=1)


# =============================================================================
# Metric Export Tests
# =============================================================================

def test_metrics_export_format(registry, sample_counter):
    """测试指标是否按 Prometheus 格式导出。"""
    # TODO: 实现测试
    #
    # 递增 counter
    sample_counter.labels(method='GET', endpoint='/test').inc()
    #
    # 生成指标输出
    output = generate_latest(registry).decode('utf-8')
    #
    # 验证输出包含预期内容
    assert 'test_requests_total' in output
    assert 'method="GET"' in output
    assert 'endpoint="/test"' in output
    assert 'test_requests_total{' in output



def test_metrics_export_multiple_metrics(registry):
    """测试多种指标类型是否可一起导出。"""
    # TODO: 实现测试
    #
    # 创建多个指标
    counter = Counter('http_requests_total', 'Total requests', registry=registry)
    gauge = Gauge('active_connections', 'Active connections', registry=registry)
    histogram = Histogram('request_duration_seconds', 'Request duration', registry=registry)
    
    # 更新指标
    counter.inc(10)
    gauge.set(42)
    histogram.observe(0.5)
    
    # 导出
    output = generate_latest(registry).decode('utf-8')
    #
    # 验证所有指标都存在
    assert 'http_requests_total 10' in output
    assert 'active_connections 42' in output
    assert 'request_duration_seconds_' in output  # histogram 包含 _bucket、_sum、_count

# =============================================================================
# Integration Tests
# =============================================================================

def test_middleware_tracks_requests():
    """测试 MetricsMiddleware 是否跟踪 HTTP 请求。"""
    # TODO: 使用 Flask 实现集成测试
    #
    # 这需要导入你真实的 Flask 应用及指标 registry
    #
    pytest.importorskip("flask")
    pytest.importorskip("psutil")
    from scripts.mock_ml_service import app
    from src.instrumentation import registry as metrics_registry

    client = app.test_client()
    response = client.get('/health')
    assert response.status_code == 200

    output = generate_latest(metrics_registry).decode('utf-8')
    assert 'http_requests_total' in output
    assert '200' in output  # 状态码



def test_prediction_metrics_tracked():
    """测试 ML 预测指标是否被正确跟踪。"""
    # TODO: 为 ML 指标实现测试
    #
    # 这会测试你真实的预测端点
    #
    pytest.importorskip("flask")
    pytest.importorskip("psutil")
    from scripts.mock_ml_service import app
    from src.instrumentation import registry as metrics_registry
    client = app.test_client()
    #
    # 发起预测请求
    response = client.post('/predict', json={'customer_tier': 'premium'})
    assert response.status_code == 200
    #
    # 验证预测指标已更新
    output = generate_latest(metrics_registry).decode('utf-8')
    assert 'model_predictions_total' in output
    assert 'model_inference_duration_seconds' in output

# =============================================================================
# Custom Metrics Tests
# =============================================================================

def test_data_drift_metric():
    """测试数据漂移检测指标。"""
    # TODO: 导入并测试你的漂移检测逻辑
    #
    np = pytest.importorskip("numpy")
    pytest.importorskip("scipy")
    pytest.importorskip("flask")
    pytest.importorskip("psutil")
    from custom_metrics import DataDriftDetector, DriftDetectionResult
    #
    # 创建检测器
    reference_data = np.random.normal(0, 1, (1000, 1))
    detector = DataDriftDetector(reference_data, ['feature_1'])
    #
    # 使用漂移数据测试
    drifted_data = np.random.normal(0.5, 1, (1000, 1))
    results = detector.detect_drift(drifted_data)
    #
    # 导出漂移指标
    detector.export_drift_metrics(results)
    #
    assert isinstance(results, list)
    assert len(results) == 1
    assert isinstance(results[0], DriftDetectionResult)



def test_model_performance_metric():
    """测试模型性能监控指标。"""
    # TODO: 测试性能监控逻辑
    #
    pytest.importorskip("numpy")
    pytest.importorskip("scipy")
    pytest.importorskip("flask")
    pytest.importorskip("psutil")
    from custom_metrics import ModelPerformanceMonitor
    
    monitor = ModelPerformanceMonitor('test_model', min_samples=10)
    #
    # 记录预测和真实标签
    for i in range(15):
        pred = 1 if i % 2 == 0 else 0
        truth = 1 if i % 2 == 0 else 0
        monitor.log_prediction(pred, truth)
    #
    # 计算指标
    metrics = monitor.calculate_metrics()
    #
    # 验证指标计算结果
    assert metrics is not None
    assert metrics.accuracy == 1.0  # 完全正确预测


# =============================================================================
# 测试辅助函数
# =============================================================================

def get_histogram_sample_value(histogram, sample_kind: str, **labels):
    """
    从 Histogram 的 collect() 结果中读取 bucket/sum/count。
    """
    sample_name = f"{histogram._name}_{sample_kind}"
    for metric in histogram.collect():
        for sample in metric.samples:
            if sample.name != sample_name:
                continue
            if all(sample.labels.get(k) == str(v) for k, v in labels.items()):
                return sample.value
    raise AssertionError(f"未找到 Histogram 样本: {sample_name} labels={labels}")


def get_metric_value(metric, **labels):
    """
    在测试中获取指标值的辅助函数。

    Args:
        metric: Prometheus 指标对象
        **labels: 标签键值对

    Returns:
        指标值
    """
    # TODO: 实现辅助函数
    #
    if labels:
        labeled_metric = metric.labels(**labels)
        return labeled_metric._value._value
    else:
        return metric._value._value



def assert_metric_exists(registry, metric_name):
    """
    断言某个指标在 registry 中存在。

    Args:
        registry: Prometheus registry
        metric_name: 指标名称
    """
    # TODO: 实现辅助函数
    #
    output = generate_latest(registry).decode('utf-8')
    assert metric_name in output, f"在输出中未找到指标 '{metric_name}'"


# =============================================================================
# 性能测试
# =============================================================================

def test_metric_performance():
    """测试指标操作是否足够快。"""
    # TODO: 实现性能测试
    #
    # 指标操作通常应非常快（单次操作 < 1ms）
    #
    registry = CollectorRegistry()
    counter = Counter('test', 'Test counter', registry=registry)
    
    import time
    start = time.time()
    for _ in range(10000):
        counter.inc()
    duration = time.time() - start
    
    # 10000 次递增应在 100ms 内完成
    assert duration < 0.1


# =============================================================================
# 异常处理测试
# =============================================================================

def test_invalid_label_values():
    """测试指标是否能处理非法标签值。"""
    # Prometheus标签名和值不允许包含某些字符（如空格、逗号、等号等），否则通常会在暴露/注册时抛出异常
    # 这里我们尝试使用非法标签值，并检查是否抛出异常或被友好处理

    from prometheus_client.core import CollectorRegistry
    import pytest
    registry = CollectorRegistry()

    # 创建计数器，准备添加非法的 label value
    from prometheus_client import Counter

    metric = Counter('illegal_test_labels', 'Test counter for illegal label values', ['animal'], registry=registry)

    # 定义一组非法的 label 值
    illegal_values = [
        "dog,cat",   # 包含逗号
        "cat=dog",   # 包含等号
        "bird fox",  # 包含空格
        "koala\n",   # 包含换行符
        "squirrel\t", # 包含制表符
        "prom$%",    # 一些特殊符号
    ]

    for val in illegal_values:
        metric.labels(val).inc()

    from prometheus_client.exposition import generate_latest
    output = generate_latest(registry).decode("utf-8")
    assert "illegal_test_labels_total" in output

def test_metric_registration_conflict():
    """测试重复指标名冲突处理。"""
    # TODO: 测试重复指标处理
    #
    # 重复注册同名指标应抛出错误
    #
    registry = CollectorRegistry()
    Counter('test', 'Test', registry=registry)
    
    with pytest.raises(ValueError):
        Counter('test', 'Test duplicate', registry=registry)



# =============================================================================
# 运行测试
# =============================================================================

if __name__ == "__main__":
    # 使用 pytest 运行测试
    pytest.main([__file__, '-v'])

    print("\n" + "="*70)
    print("测试说明")
    print("="*70)
    print("\n1. 安装 pytest：")
    print("   pip install pytest pytest-cov")
    print("\n2. 运行全部测试：")
    print("   pytest tests/test_metrics.py -v")
    print("\n3. 运行单个测试：")
    print("   pytest tests/test_metrics.py::test_counter_increment -v")
    print("\n4. 带覆盖率运行：")
    print("   pytest tests/test_metrics.py --cov=src --cov-report=html")
    print("\n5. 查看覆盖率报告：")
    print("   open htmlcov/index.html")
    print("\n" + "="*70)
