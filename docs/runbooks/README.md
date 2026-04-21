# 告警 Runbook 索引

每条 Runbook 对应 [platform/observability/prometheus/alerts.yml](../../platform/observability/prometheus/alerts.yml) 中的一条规则，便于 on-call 按步骤处理。

| 告警 | Runbook |
|------|---------|
| `ServiceDown` | [service-down.md](service-down.md) |
| `HighErrorRate` | [high-error-rate.md](high-error-rate.md) |
| `HighCPUUsage` | [high-cpu-usage.md](high-cpu-usage.md) |

## 告警数据路径（口述 / 面试用）

```mermaid
flowchart LR
  prom[Prometheus_rules]
  prom -->|evaluate| firing[Firing_alerts]
  firing -->|notify| am[Alertmanager]
  am -->|route| recv[Receiver]
  recv -->|HTTP_POST_JSON| wh[Webhook_or_null]
```

1. **Prometheus** 按 `evaluation_interval` 评估规则，满足 `for` 持续时间后进入 **Firing**。
2. **Alertmanager** 接收 `POST /api/v2/alerts`，按 `route` 的 `receiver`、`group_by`、`group_wait` 等合并与抑制。
3. **Receiver** 当前仓库为占位 **`default`**（无真实通知 URL）。生产环境通常配置 `slack_configs`、`webhook_configs` 或 PagerDuty 等。

## 配置 Webhook（示例，勿提交密钥）

在 [platform/observability/alertmanager/alertmanager.yml](../../platform/observability/alertmanager/alertmanager.yml) 中可增加第二个 receiver，例如调试用的 HTTP 接收器（[Webhook.site](https://webhook.site)、自建 echo 服务等）：

```yaml
receivers:
  - name: default
  - name: webhook_debug
    webhook_configs:
      - url: "https://webhook.site/<your-unique-path>"
        send_resolved: true
```

将 `route.receiver` 改为 `webhook_debug` 或增加 `routes` 子路由按 `severity` 分流。**敏感 URL 与 Token 不要写入 Git**；本地可用 `kubectl create secret` + `alertmanager.yaml` 引用 secret 的挂载方案（本仓库未实现，见 [../production-hardening-notes.md](../production-hardening-notes.md)）。

Alertmanager 发往 Webhook 的 body 为 **JSON 数组**，元素字段含 `status`（`firing`/`resolved`）、`labels`、`annotations`、`startsAt` 等，与 Prometheus UI 中展示的告警一致。
