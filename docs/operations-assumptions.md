# 运维假设：资源、弹性、数据与 RPO/RTO

本文档描述本仓库在 **单机 / 教学用 k3s** 场景下的默认假设，便于回答「为什么没上 HPA」「数据丢了怎么办」等问题。细节以 [deployments/kustomize/](deployments/kustomize/) 当前清单为准。

---

## 计算资源（requests / limits）

以下为**摘要**；合并前若修改 YAML，请同步更新本节。

| 工作负载 | requests（示例） | limits | 说明 |
|----------|------------------|--------|------|
| `ml-api` | cpu 50m, memory 128Mi | cpu 500m, memory 512Mi | 多副本分摊流量；limit 防止单 Pod 占满节点 |
| `prometheus` | cpu 200m, memory 512Mi | cpu 2, memory 2Gi | 大查询可能吃满 memory；单机实验需观察 OOM |
| 其他（Grafana、Alertmanager、ES、Logstash 等） | 见各 Deployment YAML | 部分仅有 requests | 未设 limit 的 Pod 在压力下可能造成 **noisy neighbor** |

**风险**：在资源紧张的单节点上，未设 **limit** 的组件可能与 Prometheus 争抢，导致查询超时或抓取抖动。

---

## 弹性：HPA、PDB

- **HorizontalPodAutoscaler（HPA）**：未配置。负载变化通过**固定副本数**（如 `ml-api` 3 副本）演示。
- **PodDisruptionBudget（PDB）**：未配置。维护窗口内不保证「最少可用」副本数。

**原因（口述用）**：当前目标是 **可重复的演示栈** 与较低心智负担；单节点 k3s 上 HPA/PDB 收益有限，且依赖 metrics-server 与容量规划话题，故列为 out of scope。

---

## Prometheus 与 Elasticsearch 数据

- **Prometheus**：数据目录为 PVC `prometheus-data`；进程参数含 `--storage.tsdb.retention.time=30d` 与 `--storage.tsdb.retention.size=10GB`（见 [prometheus.yaml](../deployments/kustomize/prometheus.yaml)）。**单副本**：无内置 HA；节点或 PVC 故障可能导致**观测数据中断**。
- **Elasticsearch**：StatefulSet + PVC；索引生命周期（ILM）未在仓库内完整建模。

**备份**：本仓库**不包含**定时快照、Velero、或 ES 快照仓库配置；视为 **OutOfScope**。

---

## RPO / RTO（学习栈声明）

| 维度 | 假设 |
|------|------|
| **RPO**（可接受数据丢失窗口） | 可接受丢失「自上次无备份以来的」Prometheus TSDB 与 ES 数据；不保证跨下架保留。`k8s-down.sh` 删除命名空间**含 PVC**。 |
| **RTO**（恢复服务时间） | 依赖重新执行 `k8s-up.sh`、镜像拉取/导入与 ES 启动时间；未做 SLA 数字承诺。 |

生产环境应单独定义 RPO/RTO，并配套备份与演练。

---

## Prometheus 单副本（面试常见问题）

- **现状**：单 Prometheus Deployment，便于理解与排障。
- **若需 HA**：常见路径为 **Thanos / Mimir / Cortex** 长期存储与联邦，或双副本 + 反亲和与去重规则；超出本仓库范围，在 [requirements-matrix.md](requirements-matrix.md) 中标记为 Partial / OutOfScope。
