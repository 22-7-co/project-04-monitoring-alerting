# Runbook：`HighCPUUsage`

## 规则引用

- **Alert 名称**：`HighCPUUsage`
- **规则文件**：[platform/observability/prometheus/alerts.yml](../../platform/observability/prometheus/alerts.yml)（`infrastructure_alerts`）
- **表达式（摘要）**：基于 `node_cpu_seconds_total{mode="idle"}` 推算的 CPU 使用率 **> 80%**，**持续时间**：`5m`
- **标签**：`severity: warning`，`component: infrastructure`

## 用户影响

节点或实例 CPU 长期高位，可能导致**调度延迟、P99 升高、甚至 OOM 前兆**；本告警为 **Warning**，一般不单独作为「立即宕机」页，但应纳入容量规划。

## 先看什么

1. PromQL（与规则一致思路）：`100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`
2. **Grafana / Prometheus**：同一 `instance` 的负载与内存是否同步升高。
3. `kubectl top nodes` / `kubectl top pods -A --sort-by=cpu`（需 metrics-server 时可用）。

## 常见根因

| 根因 | 处理方向 |
|------|----------|
| 压测或批处理 | 与业务确认是否预期 |
| 某 Pod 无 limit 狂占 CPU | 考虑设置 requests/limits 或迁走热点 Pod |
| 节点过少 | 水平扩容节点或分散工作负载 |

## 操作步骤

1. 确认告警中的 `instance` 对应哪台节点或 exporter。
2. 列出高 CPU Pod：`kubectl top pods -A`（若集群支持）。
3. 与 `ml-api`、Elasticsearch 等大内存 CPU 组件的发布/流量关联分析。

## 恢复判据

- 上述使用率计算结果 **≤ 80%** 持续超过告警 `for` 窗口。
- 若已做限流/扩容，确认业务延迟与错误率未恶化（参见 [high-error-rate.md](high-error-rate.md)）。
