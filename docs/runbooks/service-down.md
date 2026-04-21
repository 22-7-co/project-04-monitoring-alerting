# Runbook：`ServiceDown`

## 规则引用

- **Alert 名称**：`ServiceDown`
- **规则文件**：[platform/observability/prometheus/alerts.yml](../../platform/observability/prometheus/alerts.yml)（`infrastructure_alerts`）
- **表达式**：`up == 0`，**持续时间**：`2m`
- **标签**：`severity: critical`，`component: infrastructure`

## 用户影响

`up` 为 0 表示 Prometheus **无法从该抓取目标拿到指标**，可能是进程挂了、网络不通、或 scrape 配置错误。影响取决于 **job**：

- **`kubernetes-ml-api-pods`**：可能影响对 `ml-api` 健康与 SLO 的观测；若业务 Pod 仍存活，用户未必立刻感知，但**失去可观测性**。
- **`node-exporter`**：失去该节点系统指标。
- **`prometheus`（自监控 job）**：若仅为自抓异常，需区分是否误配。

## 先看什么

1. **Prometheus UI** → Status → Targets：过滤 `State != UP`，确认失败原因（`Connection refused`、`context deadline exceeded` 等）。
2. 常用 PromQL：`up == 0` 或 `up{job="kubernetes-ml-api-pods"} == 0`。
3. **Grafana**（若有 Node / 应用大盘）：同一时间窗是否数据断档。

## 常见根因

| 根因 | 线索 |
|------|------|
| Pod CrashLoop / OOM | `kubectl get pods` 非 Running |
| 端口或 path 与注解不一致 | Target 错误信息含 404 / connection refused |
| 网络策略或 CNI | 仅跨命名空间或跨节点失败 |
| 目标进程未监听 | scrape 地址错 |

## 操作步骤

```bash
kubectl -n monitoring-stack get pods -o wide
kubectl -n monitoring-stack describe pod -l app=ml-api   # 示例：ml-api 不可抓时
kubectl -n monitoring-stack logs deploy/ml-api --tail=100
```

若 `node-exporter` 相关：检查 DaemonSet 与节点是否 Ready。

## 恢复判据

- Prometheus Targets 中对应 job **恢复为 UP**。
- `up{instance="<该实例>"} == 1` 持续稳定至少一个 scrape 间隔以上。
- 告警在 Alertmanager 中进入 **resolved**（若已接通知渠道）。
