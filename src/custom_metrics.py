"""
用于监控的自定义 ML 指标

本模块实现了超出标准应用监控范围的 ML 专属指标：
- 数据漂移检测（特征分布偏移）
- 模型性能退化跟踪
- 预测置信度分析
- 特征重要性漂移
- 数据质量监控

学习目标：
- 使用统计检验实现数据漂移检测
- 跟踪模型性能的时间变化
- 监控数据质量问题
- 理解 ML 可观测性的专属挑战
- 为 Prometheus 构建自定义指标导出

参考资料：
- 统计检验：https://docs.scipy.org/doc/scipy/reference/stats.html
- Evidently AI：https://evidentlyai.com/
- ML 监控最佳实践：https://christophergs.com/machine%20learning/2020/03/14/how-to-monitor-machine-learning-models/
"""

import numpy as np
from scipy import stats
from scipy.spatial.distance import jensenshannon
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime
import json

# TODO: 从 instrumentation.py 导入你定义的指标
from instrumentation import (
    data_drift_score,
    model_accuracy,
    missing_features_total,
    model_prediction_confidence
)

logger = logging.getLogger(__name__)


# =============================================================================
# 结果数据类
# =============================================================================

@dataclass
class DriftDetectionResult:
    """漂移检测结果。"""
    feature_name: str
    statistic: float
    p_value: float
    is_drift: bool
    test_method: str
    timestamp: datetime


@dataclass
class ModelPerformanceMetrics:
    """模型在一段时间内的性能指标。"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    sample_count: int
    timestamp: datetime


# =============================================================================
# 数据漂移检测
# =============================================================================

class DataDriftDetector:
    """
    使用统计检验检测输入数据分布偏移。

    该类实现了多种漂移检测方法：
    1. Kolmogorov-Smirnov（KS）检验：适用于连续特征
    2. Population Stability Index（PSI）：适用于分箱分布
    3. Jensen-Shannon Divergence：适用于概率分布
    4. 卡方检验：适用于离散/类别特征

    用法：
        # 使用参考数据（训练集）初始化
        detector = DataDriftDetector(
            reference_data=X_train,
            feature_names=feature_names,
            threshold=0.05
        )

        # 检测生产数据是否发生漂移
        drift_results = detector.detect_drift(X_production)

        # 导出指标到 Prometheus
        detector.export_drift_metrics()
    """

    def __init__(
        self,
        reference_data: np.ndarray,
        feature_names: List[str],
        threshold: float = 0.05,
        method: str = 'ks'
    ):
        """
        使用参考分布初始化漂移检测器。

        Args:
            reference_data: 训练数据分布（n_samples, n_features）
            feature_names: 特征名列表
            threshold: 漂移判定的 p 值阈值（默认：0.05）
            method: 漂移检测方法（'ks'、'psi'、'js'、'chi2'）
        """
        # TODO: 保存参考数据和参数
        # self.reference_data = reference_data
        # self.feature_names = feature_names
        # self.threshold = threshold
        # self.method = method
        # self.n_features = reference_data.shape[1]
        #
        # # 校验输入
        # if len(feature_names) != self.n_features:
        #     raise ValueError(
        #         f"特征名数量 ({len(feature_names)}) "
        #         f"必须与特征数 ({self.n_features}) 一致"
        #     )

        pass  # 实现后删除

    def kolmogorov_smirnov_test(
        self,
        reference: np.ndarray,
        current: np.ndarray
    ) -> Tuple[float, float]:
        """
        执行 Kolmogorov-Smirnov 检验以检测分布偏移。

        KS 检验会比较两个分布并返回：
        - statistic：两条 CDF 的最大距离（0-1）
        - p_value：两个分布相同的概率

        Args:
            reference: 参考分布（1D 数组）
            current: 当前待检分布（1D 数组）

        Returns:
            (statistic, p_value)
        """
        # TODO: 使用 scipy.stats.ks_2samp 实现 KS 检验
        #
        # 示例：
        # statistic, p_value = stats.ks_2samp(reference, current)
        #
        # 解释：
        # - statistic 越接近 0，分布越相似
        # - statistic 越接近 1，分布差异越大
        # - p_value < threshold：拒绝原假设（检测到漂移）
        #
        # return statistic, p_value

        pass  # 实现后删除

    def population_stability_index(
        self,
        reference: np.ndarray,
        current: np.ndarray,
        bins: int = 10
    ) -> float:
        """
        计算 Population Stability Index（PSI）。

        PSI 基于分箱直方图度量分布偏移：
        - PSI < 0.1：变化不显著
        - PSI 0.1-0.25：中等变化
        - PSI > 0.25：显著变化

        公式：
        PSI = Σ (current% - reference%) * ln(current% / reference%)

        Args:
            reference: 参考分布
            current: 当前分布
            bins: 直方图分箱数量

        Returns:
            PSI 分数（0 表示一致，越高表示漂移越大）
        """
        # TODO: 实现 PSI 计算
        #
        # 步骤：
        # 1. 基于参考数据创建直方图分箱
        #    ref_hist, bin_edges = np.histogram(reference, bins=bins)
        #    cur_hist, _ = np.histogram(current, bins=bin_edges)
        #
        # 2. 转为占比
        #    ref_pct = ref_hist / len(reference)
        #    cur_pct = cur_hist / len(current)
        #
        # 3. 避免除零（加入微小 epsilon）
        #    epsilon = 1e-10
        #    ref_pct = np.where(ref_pct == 0, epsilon, ref_pct)
        #    cur_pct = np.where(cur_pct == 0, epsilon, cur_pct)
        #
        # 4. 计算 PSI
        #    psi = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
        #
        # return psi

        pass  # 实现后删除

    def jensen_shannon_divergence(
        self,
        reference: np.ndarray,
        current: np.ndarray,
        bins: int = 50
    ) -> float:
        """
        计算两组分布之间的 Jensen-Shannon divergence。

        JS 散度具有对称性，且范围在 [0, 1]：
        - 0：分布完全一致
        - 1：分布完全不同

        Args:
            reference: 参考分布
            current: 当前分布
            bins: 直方图分箱数量

        Returns:
            JS 散度分数（0-1）
        """
        # TODO: 实现 JS 散度计算
        #
        # 步骤：
        # 1. 创建归一化直方图
        #    ref_hist, bin_edges = np.histogram(reference, bins=bins, density=True)
        #    cur_hist, _ = np.histogram(current, bins=bin_edges, density=True)
        #
        # 2. 归一化为概率分布
        #    ref_prob = ref_hist / np.sum(ref_hist)
        #    cur_prob = cur_hist / np.sum(cur_hist)
        #
        # 3. 计算 JS 散度
        #    from scipy.spatial.distance import jensenshannon
        #    js_distance = jensenshannon(ref_prob, cur_prob)
        #
        # return js_distance

        pass  # 实现后删除

    def detect_drift(
        self,
        current_data: np.ndarray
    ) -> List[DriftDetectionResult]:
        """
        检测所有特征是否发生漂移。

        Args:
            current_data: 当前生产数据（n_samples, n_features）

        Returns:
            每个特征的漂移检测结果列表
        """
        # TODO: 实现全特征漂移检测
        #
        # 伪代码：
        # results = []
        #
        # for i, feature_name in enumerate(self.feature_names):
        #     reference_feature = self.reference_data[:, i]
        #     current_feature = current_data[:, i]
        #
        #     # 选择检测方法
        #     if self.method == 'ks':
        #         statistic, p_value = self.kolmogorov_smirnov_test(
        #             reference_feature, current_feature
        #         )
        #         is_drift = p_value < self.threshold
        #
        #     elif self.method == 'psi':
        #         statistic = self.population_stability_index(
        #             reference_feature, current_feature
        #         )
        #         p_value = None
        #         is_drift = statistic > 0.25  # PSI 阈值
        #
        #     elif self.method == 'js':
        #         statistic = self.jensen_shannon_divergence(
        #             reference_feature, current_feature
        #         )
        #         p_value = None
        #         is_drift = statistic > 0.5  # JS 阈值
        #
        #     # 构建结果对象
        #     result = DriftDetectionResult(
        #         feature_name=feature_name,
        #         statistic=statistic,
        #         p_value=p_value,
        #         is_drift=is_drift,
        #         test_method=self.method,
        #         timestamp=datetime.now()
        #     )
        #
        #     results.append(result)
        #
        #     # 记录漂移日志
        #     if is_drift:
        #         logger.warning(
        #             f"在 {feature_name} 上检测到漂移："
        #             f"statistic={statistic:.4f}, p_value={p_value}"
        #         )
        #
        # return results

        pass  # 实现后删除

    def export_drift_metrics(self, drift_results: List[DriftDetectionResult]):
        """
        将漂移检测结果导出到 Prometheus 指标。

        Args:
            drift_results: 漂移检测结果列表
        """
        # TODO: 更新 Prometheus 漂移指标
        #
        # for result in drift_results:
        #     # 更新漂移分数 Gauge
        #     data_drift_score.labels(
        #         feature_name=result.feature_name
        #     ).set(result.statistic)
        #
        #     # 写入应用日志（供 Elasticsearch 检索）
        #     logger.info(
        #         "漂移检测结果",
        #         extra={
        #             'feature_name': result.feature_name,
        #             'statistic': result.statistic,
        #             'p_value': result.p_value,
        #             'is_drift': result.is_drift,
        #             'method': result.test_method
        #         }
        #     )

        pass  # 实现后删除


# =============================================================================
# 模型性能监控
# =============================================================================

class ModelPerformanceMonitor:
    """
    按时间维度监控模型性能指标。

    跟踪内容：
    - Accuracy、Precision、Recall、F1
    - 性能退化告警
    - 真实标签反馈闭环
    - 混淆矩阵跟踪

    用法：
        monitor = ModelPerformanceMonitor(model_name='resnet50')

        # 记录预测
        monitor.log_prediction(prediction=1, ground_truth=1)

        # 计算指标（收集到足够真实标签后）
        metrics = monitor.calculate_metrics()

        # 检查是否退化
        is_degraded = monitor.check_degradation(baseline_accuracy=0.90)
    """

    def __init__(self, model_name: str, min_samples: int = 100):
        """
        初始化性能监控器。

        Args:
            model_name: 被监控模型名称
            min_samples: 计算指标前所需最小样本数
        """
        # TODO: 初始化监控器
        # self.model_name = model_name
        # self.min_samples = min_samples
        # self.predictions = []
        # self.ground_truth = []
        # self.prediction_timestamps = []

        pass  # 实现后删除

    def log_prediction(
        self,
        prediction: int,
        ground_truth: Optional[int] = None,
        prediction_id: Optional[str] = None
    ):
        """
        记录一次预测及可选真实标签。

        Args:
            prediction: 模型预测结果（类别索引）
            ground_truth: 真实标签（可选，可能稍后到达）
            prediction_id: 用于后续匹配真实标签的唯一 ID
        """
        # TODO: 存储预测结果
        #
        # self.predictions.append(prediction)
        # if ground_truth is not None:
        #     self.ground_truth.append(ground_truth)
        # self.prediction_timestamps.append(datetime.now())
        #
        # 注意：在生产环境中，你可能需要用数据库保存预测结果，
        # 并与后续到达的真实标签进行匹配

        pass  # 实现后删除

    def add_ground_truth(self, prediction_id: str, ground_truth: int):
        """
        为历史预测补充真实标签。

        这用于模拟反馈闭环：真实标签在预测发生后才到达。

        Args:
            prediction_id: 预测 ID
            ground_truth: 真实标签
        """
        # TODO: 实现真实标签反馈
        #
        # 在真实系统中，你需要：
        # 1. 按 ID 查找预测记录
        # 2. 存储真实标签
        # 3. 更新指标

        pass  # 实现后删除

    def calculate_metrics(self) -> Optional[ModelPerformanceMetrics]:
        """
        基于预测与真实标签计算性能指标。

        Returns:
            样本足够时返回 ModelPerformanceMetrics，否则返回 None
        """
        # TODO: 实现指标计算
        #
        # if len(self.ground_truth) < self.min_samples:
        #     logger.warning(
        #         f"样本不足，无法计算指标 "
        #         f"({len(self.ground_truth)} / {self.min_samples})"
        #     )
        #     return None
        #
        # # 导入 sklearn 指标
        # from sklearn.metrics import (
        #     accuracy_score,
        #     precision_score,
        #     recall_score,
        #     f1_score
        # )
        #
        # # 计算指标
        # accuracy = accuracy_score(self.ground_truth, self.predictions)
        # precision = precision_score(
        #     self.ground_truth,
        #     self.predictions,
        #     average='weighted'
        # )
        # recall = recall_score(
        #     self.ground_truth,
        #     self.predictions,
        #     average='weighted'
        # )
        # f1 = f1_score(
        #     self.ground_truth,
        #     self.predictions,
        #     average='weighted'
        # )
        #
        # metrics = ModelPerformanceMetrics(
        #     accuracy=accuracy,
        #     precision=precision,
        #     recall=recall,
        #     f1_score=f1,
        #     sample_count=len(self.ground_truth),
        #     timestamp=datetime.now()
        # )
        #
        # # 更新 Prometheus 指标
        # model_accuracy.labels(model_name=self.model_name).set(accuracy)
        #
        # # 记录日志
        # logger.info(
        #     f"模型性能指标：accuracy={accuracy:.4f}, "
        #     f"precision={precision:.4f}, recall={recall:.4f}, f1={f1:.4f}"
        # )
        #
        # return metrics

        pass  # 实现后删除

    def check_degradation(
        self,
        baseline_accuracy: float,
        threshold: float = 0.1
    ) -> bool:
        """
        检查模型性能是否显著退化。

        Args:
            baseline_accuracy: 期望基线准确率
            threshold: 退化阈值（如 0.1 代表下降 10%）

        Returns:
            检测到退化返回 True，否则返回 False
        """
        # TODO: 实现退化检测
        #
        # if len(self.ground_truth) < self.min_samples:
        #     return False
        #
        # from sklearn.metrics import accuracy_score
        # current_accuracy = accuracy_score(self.ground_truth, self.predictions)
        # degradation = baseline_accuracy - current_accuracy
        #
        # if degradation > threshold:
        #     logger.error(
        #         f"检测到性能退化！"
        #         f"基线：{baseline_accuracy:.4f}, "
        #         f"当前：{current_accuracy:.4f}, "
        #         f"退化幅度：{degradation:.4f}"
        #     )
        #     return True
        #
        # return False

        pass  # 实现后删除


# =============================================================================
# 预测置信度分析
# =============================================================================

class ConfidenceAnalyzer:
    """
    按时间分析预测置信度分数。

    跟踪内容：
    - 置信度分布
    - 低置信度预测
    - 置信度与准确率相关性
    - 置信度漂移

    用法：
        analyzer = ConfidenceAnalyzer()
        analyzer.log_confidence(confidence=0.95, is_correct=True)
        stats = analyzer.get_statistics()
    """

    def __init__(self, window_size: int = 1000):
        """
        初始化置信度分析器。

        Args:
            window_size: 用于分析的最近预测数量窗口
        """
        # TODO: 初始化分析器
        # self.window_size = window_size
        # self.confidences = []
        # self.correctness = []  # 预测是否正确

        pass  # 实现后删除

    def log_confidence(self, confidence: float, is_correct: Optional[bool] = None):
        """
        记录预测置信度。

        Args:
            confidence: 预测置信度（0-1）
            is_correct: 预测是否正确（可选）
        """
        # TODO: 存储置信度
        #
        # self.confidences.append(confidence)
        # if is_correct is not None:
        #     self.correctness.append(is_correct)
        #
        # # 仅保留最近窗口
        # if len(self.confidences) > self.window_size:
        #     self.confidences = self.confidences[-self.window_size:]
        #     self.correctness = self.correctness[-self.window_size:]

        pass  # 实现后删除

    def get_statistics(self) -> Dict[str, float]:
        """
        计算置信度统计值。

        Returns:
            包含统计项（均值、中位数、标准差、分位数）的字典
        """
        # TODO: 计算统计值
        #
        # if len(self.confidences) == 0:
        #     return {}
        #
        # confidences_array = np.array(self.confidences)
        #
        # stats = {
        #     'mean': np.mean(confidences_array),
        #     'median': np.median(confidences_array),
        #     'std': np.std(confidences_array),
        #     'min': np.min(confidences_array),
        #     'max': np.max(confidences_array),
        #     'p25': np.percentile(confidences_array, 25),
        #     'p50': np.percentile(confidences_array, 50),
        #     'p75': np.percentile(confidences_array, 75),
        #     'p95': np.percentile(confidences_array, 95),
        #     'count': len(self.confidences)
        # }
        #
        # # 若有真实标签，计算校准分数
        # if len(self.correctness) > 0:
        #     # 按置信度分箱比较真实准确率
        #     # 用于判断高置信度是否对应高准确率
        #     stats['calibration_score'] = self._calculate_calibration()
        #
        # return stats

        pass  # 实现后删除

    def _calculate_calibration(self) -> float:
        """
        计算模型校准分数。

        校准良好的模型：90% 置信度的预测大约有 90% 正确率。

        Returns:
            校准误差（越低越好）
        """
        # TODO: 实现校准计算
        #
        # 这是进阶内容，对初级工程师可选
        #
        # 提示：使用 sklearn.calibration.calibration_curve

        return 0.0


# =============================================================================
# 数据质量监控
# =============================================================================

class DataQualityMonitor:
    """
    监控生产请求中的数据质量问题。

    检查项：
    - 缺失值
    - 超范围值
    - 类型错误
    - Schema 变化
    - 编码错误
    """

    def __init__(self, expected_schema: Dict[str, str]):
        """
        初始化数据质量监控器。

        Args:
            expected_schema: 期望 Schema {feature_name: data_type}
        """
        # TODO: 初始化监控器
        # self.expected_schema = expected_schema
        # self.issue_counts = {
        #     'missing': {},
        #     'out_of_range': {},
        #     'type_error': {},
        #     'schema_mismatch': 0
        # }

        pass  # 实现后删除

    def validate_request(self, data: Dict) -> Dict[str, List[str]]:
        """
        校验进入系统的请求数据。

        Args:
            data: 请求数据字典

        Returns:
            发现的问题字典 {issue_type: [feature_names]}
        """
        # TODO: 实现校验
        #
        # issues = {
        #     'missing': [],
        #     'type_error': [],
        #     'out_of_range': []
        # }
        #
        # # 检查缺失特征
        # for feature_name in self.expected_schema:
        #     if feature_name not in data:
        #         issues['missing'].append(feature_name)
        #         missing_features_total.labels(
        #             feature_name=feature_name
        #         ).inc()
        #
        # # 检查数据类型
        # for feature_name, value in data.items():
        #     expected_type = self.expected_schema.get(feature_name)
        #     if expected_type and not isinstance(value, eval(expected_type)):
        #         issues['type_error'].append(feature_name)
        #
        # # 检查取值范围（你需要自行定义规则）
        # # 示例：if 'age' not in range(0, 120):
        # #     issues['out_of_range'].append('age')
        #
        # return issues

        pass  # 实现后删除


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    print("自定义 ML 指标模块")
    print("=" * 50)

    # TODO: 添加使用示例
    #
    # 示例 1：漂移检测
    # print("\n1. 测试漂移检测：")
    # # 生成参考数据
    # np.random.seed(42)
    # reference_data = np.random.normal(0, 1, (1000, 3))
    # feature_names = ['feature_1', 'feature_2', 'feature_3']
    #
    # # 创建检测器
    # detector = DataDriftDetector(
    #     reference_data=reference_data,
    #     feature_names=feature_names,
    #     threshold=0.05,
    #     method='ks'
    # )
    #
    # # 使用漂移数据测试（均值偏移）
    # drifted_data = np.random.normal(0.5, 1, (1000, 3))
    # drift_results = detector.detect_drift(drifted_data)
    #
    # for result in drift_results:
    #     print(f"{result.feature_name}: drift={result.is_drift}, "
    #           f"statistic={result.statistic:.4f}, p_value={result.p_value:.4f}")

    # 示例 2：性能监控
    # print("\n2. 测试性能监控：")
    # monitor = ModelPerformanceMonitor('test_model', min_samples=10)
    #
    # # 模拟预测
    # for i in range(20):
    #     pred = np.random.randint(0, 2)
    #     truth = np.random.randint(0, 2)
    #     monitor.log_prediction(pred, truth)
    #
    # # 计算指标
    # metrics = monitor.calculate_metrics()
    # if metrics:
    #     print(f"Accuracy: {metrics.accuracy:.4f}")
    #     print(f"F1 Score: {metrics.f1_score:.4f}")

    print("\n请先实现 TODO 并取消注释示例后再测试！")
