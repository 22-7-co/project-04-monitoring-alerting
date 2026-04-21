# SLO 与可观测性深化（文档轨道 B）

本仓库以 **指标 + 日志** 为主；本页说明如何在**不新增组件**的前提下，用现有 Prometheus / Grafana 讲清 **SLO** 与 **运维告警** 的差异，并给出可落地的下一步（可选实现）。

---

## SLI / SLO / Error budget（概念）

- **SLI**（Service Level Indicator）：可量化服务好坏的指标，例如「`/health` 成功比例」或「`/predict` P95 延迟 < 500ms 的比例」。
- **SLO**（Service Level Objective）：对 SLI 的承诺目标，例如「每月 99.9% 的 `/health` 探测成功」。
- **Error budget**：`1 - SLO` 允许的「坏」比例；budget 消耗过快时再做发布或架构决策。

---

## 与本仓库告警的关系

| 类型 | 示例（见 [platform/observability/prometheus/alerts.yml](../platform/observability/prometheus/alerts.yml)） | 升级策略建议 |
|------|----------------------------------------------------------------|--------------|
| **用户向 SLO** | 可由「`up` + job=ml-api」或「5xx 比例 + 延迟」组合表达；`HighSLOBurnRate` 为向此方向预留的规则名 | 高优先级页、需产品/研发参与 |
| **运维/容量** | `HighCPUUsage`、`LowDiskSpace` | 通常先工单或白天处理，避免与用户体验直接混淆 |

**口述要点**：CPU 高**不一定**违反 SLO；SLO 应尽可能贴近**用户可感知**的可用性与延迟。

---

## Grafana 面板草图（自行添加时的 PromQL 思路）

以下为**示意**，非已提交 JSON；可在 Grafana Explore 中验证后保存为面板。

1. **可用性 SLI（7d）**：`avg_over_time((sum(up{job=~"kubernetes-ml-api-pods"}) / count(up{job=~"kubernetes-ml-api-pods"}))[7d:])`（按你实际 `job` 标签调整）。
2. **错误预算消耗（示意）**：将「实际 5xx 率」与「月度允许 5xx 率」对比，可用 `HighErrorRate` 同源指标做 ratio 图。

---

## 轨道 A：Tracing（未在本仓库实现）

若后续引入 **OpenTelemetry + Jaeger/Tempo**，建议：

- 在日志中注入 **trace_id**，与现有 Filebeat → ES → Kibana 链路关联；
- 指标仍由 Prometheus 负责聚合，trace 负责单请求因果。

当前状态：**OutOfScope**；面试时可口述边界。
