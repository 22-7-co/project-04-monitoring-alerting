# STAR 排障案例（与仓库一致，可口述）

本案例与 [requirements-matrix.md](../requirements-matrix.md) 中的 **FR-2.1（Grafana 数据源）**、**FR-1.1（Prometheus 可用）** 验证列相关：问题表现为「可视化不可用」，根因在**解析路径**而非应用代码。

## Situation（情境）

在 Kubernetes 命名空间 `monitoring-stack` 中，Grafana 已 Running，但数据源健康检查失败或面板查询报错，例如对 Prometheus `query_range` 的请求返回 **EOF** 或 HTTP 500；Prometheus Pod 内自检 `localhost:9090` 却正常。

## Task（任务）

在不大改架构的前提下，恢复 **Grafana → Prometheus** 查询链路，并说明根因以便同类环境不再踩坑。

## Action（行动）

1. **分层验证**：在 Grafana Pod 内对 `http://prometheus:9090` 与 **Service ClusterIP** 分别执行 `curl` / `nslookup`。
2. **对比结果**：若主机名解析到 **非集群网段**（例如 `198.18.0.0/15` 一类常见于 Fake-IP / 透明代理的地址），而 ClusterIP 访问返回 200，则判定为 **DNS 或上游污染**，而非 Prometheus 进程故障。
3. **处理**：关闭或调整宿主机/集群 DNS 链路上的干扰（如代理 TUN 模式）；修正后 Grafana 数据源恢复；文档中记录「集群内解析应得到 ClusterIP」。

## Result（结果）

- 数据源与面板查询恢复；**Prometheus 无需改镜像或配置**。
- 沉淀经验：**先区分「业务挂了」与「名字解析/流量走错路」**，用同 Pod 内对比 DNS 与直连 IP 可快速定性。

**矩阵对照**：验证 Grafana 数据源对应 [requirements-matrix.md](../requirements-matrix.md) 表中 **FR-2.1** 行；Prometheus 可用性对应 **FR-1.1**。
