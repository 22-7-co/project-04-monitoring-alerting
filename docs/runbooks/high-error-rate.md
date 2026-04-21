# Runbook：`HighErrorRate`

## 规则引用

- **Alert 名称**：`HighErrorRate`
- **规则文件**：[platform/observability/prometheus/alerts.yml](../../platform/observability/prometheus/alerts.yml)（`application_alerts`）
- **表达式（摘要）**：5xx 速率占全部 HTTP 请求速率比例 **> 5%**，**持续时间**：`5m`
- **标签**：`severity: critical`，`component: application`

## 用户影响

HTTP **5xx** 比例升高，通常表示**服务端错误**或依赖失败；若持续 5 分钟，用户可能遇到失败请求或重试风暴。

## 先看什么

1. PromQL：`sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100`
2. 按端点拆分：`sum by (handler) (rate(http_requests_total{status=~"5.."}[5m]))`
3. **Grafana** 预置 ml-api 大盘（若有）：错误率、状态码分布、延迟。
4. **Kibana**：按时间与 `level`/`message` 过滤 `ml-api` 日志（若已采集）。

## 常见根因

| 根因 | 处理方向 |
|------|----------|
| 部署引入回归 | 对比发布时间线与告警时间；考虑回滚 |
| 依赖超时/503 | 查下游与健康检查 |
| 故意故障注入或压测 | 本仓库 `scripts/simulate_production_traffic.py` 会打 `/error`，确认是否为预期流量 |

## 操作步骤

1. 确认是否为**预期** 5xx（例如演示环境的 `/error` 路由）。
2. `kubectl -n monitoring-stack logs deploy/ml-api --tail=200 --since=15m`
3. 必要时临时扩容或限流（本仓库未内置 HPA，见 [../operations-assumptions.md](../operations-assumptions.md)）。

## 恢复判据

- 5xx 占比 PromQL 回到阈值以下并稳定超过 `for` 时长。
- `/health` 与核心业务路径抽样返回 2xx。
