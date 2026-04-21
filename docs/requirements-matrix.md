# 需求与实现对照矩阵（FR → 仓库产物）

列含义：**状态** 取 `Done`（已满足） / `Partial`（部分满足） / `DocOnly`（仅文档或占位） / `OutOfScope`（本仓库明确不做或未实现）。

| FR 编号 | 需求摘要 | 实现位置 | 状态 | 验证方式 | 备注 |
|---------|----------|----------|------|----------|------|
| FR-1.1 | Prometheus 2.47+、持久化、保留约 30 天 | [deployments/kustomize/prometheus.yaml](deployments/kustomize/prometheus.yaml)、[platform/observability/prometheus/prometheus-k8s.yml](platform/observability/prometheus/prometheus-k8s.yml) | Done | `kubectl -n monitoring-stack get deploy prometheus`；UI：`kubectl get svc -n monitoring-stack prometheus` + NodePort | Compose 不要求；HA 多副本未做 |
| FR-1.2 | 服务发现、relabel | [platform/observability/prometheus/prometheus-k8s.yml](platform/observability/prometheus/prometheus-k8s.yml) `kubernetes_sd_configs`；Pod 注解见 [deployments/kustomize/ml-api.yaml](deployments/kustomize/ml-api.yaml) | Partial | Prometheus UI → Status → Targets | 文件 SD / 纯 DNS SD 未单独配置 |
| FR-1.3 | Node 级基础设施指标 | [deployments/kustomize/node-exporter.yaml](deployments/kustomize/node-exporter.yaml)；Prometheus job `node-exporter` | Done | PromQL：`up{job="node-exporter"}` | 依赖 DaemonSet 调度到节点 |
| FR-1.4 | HTTP 指标、直方图、错误率等 | [src/instrumentation.py](src/instrumentation.py)；镜像 [apps/ml-api/](apps/ml-api/) | Partial | `curl :30500/metrics`（NodePort 见文档） | 以实际埋点为准；与 FR 逐条对比见代码 |
| FR-1.5 | ML 专属指标、漂移等 | `instrumentation` / [src/custom_metrics.py](src/custom_metrics.py) 等 | Partial | `/metrics` 与 Grafana 预置大盘 | 部分指标可能为占位或简化 |
| FR-2.1 | Grafana 10.x、数据源 provisioning | [deployments/kustomize/grafana.yaml](deployments/kustomize/grafana.yaml)、[platform/observability/grafana/datasources.yml](platform/observability/grafana/datasources.yml) | Done | NodePort 30300；Save & test 数据源 | 默认 admin；生产 RBAC 见加固文档 |
| FR-2.2～2.5 | 多类仪表盘 | [platform/observability/grafana/dashboards/](platform/observability/grafana/dashboards/)、kustomize ConfigMap | Partial | Grafana UI | 预置以 ml-api 为主；FR 所列全量面板未保证齐全 |
| FR-3.1 | ELK 栈 | [deployments/kustomize/](deployments/kustomize/) 中 elasticsearch、logstash、kibana、filebeat | Done | Kibana NodePort；ES 集群健康 | 非 compose 单机端口 |
| FR-3.2～3.3 | 日志采集与解析 | [platform/logging/](platform/logging/)、Filebeat DaemonSet | Partial | Kibana Discover | 「无丢失」未做形式化保证 |
| FR-4.1 | Alertmanager 路由与接收端 | [deployments/kustomize/alertmanager.yaml](deployments/kustomize/alertmanager.yaml)、[platform/observability/alertmanager/alertmanager.yml](platform/observability/alertmanager/alertmanager.yml) | Partial | AM UI 30093；通知路径见 [docs/runbooks/README.md](runbooks/README.md) | 默认 receiver；Webhook 示例见 Runbook 索引 |
| FR-4.2～4.3 | 基础设施与应用告警 | [platform/observability/prometheus/alerts.yml](platform/observability/prometheus/alerts.yml) | Partial | Prometheus → Alerts；[docs/runbooks/README.md](runbooks/README.md) | Runbook 覆盖 `ServiceDown` / `HighErrorRate` / `HighCPUUsage`；其余规则按需补充 |

维护：合并影响上述路径的 PR 时，更新本表 **状态 / 验证方式 / 备注** 列。

**口述与案例**：面试 STAR 案例见 [interview-orals/star-case.md](interview-orals/star-case.md)；SLO 分层说明见 [slo-and-observability-depth.md](slo-and-observability-depth.md)。
