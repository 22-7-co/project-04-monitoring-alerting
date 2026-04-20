# 全栈跑在 k8s（一键上架 / 一键下架）

命名空间：`monitoring-stack`。包含 **ml-api**（3 副本）、**Prometheus**、**Alertmanager**、**Grafana**、**Node Exporter**、**Elasticsearch**、**Logstash**、**Kibana**、**Filebeat**。

## 前置

- 本机已安装并运行 **k8s**，且存在可用的 `KUBECONFIG`（默认 `/etc/rancher/k3s/k3s.yaml`）。
- 已安装 **Docker**（用于构建 `ml-api:dev`）、**kubectl**。
- 需提供可用 **StorageClass**（如 `local-path`）；Elasticsearch / Prometheus / Grafana 等使用 PVC。

若 Elasticsearch 起不来，宿主机可执行：`sudo sysctl -w vm.max_map_count=262144`（按需写入 `/etc/sysctl.d/`）。

## 一键上架

在项目根目录：

```bash
./ops/scripts/k8s-up.sh
```

- 默认会 `docker build` 并尝试导入本地集群运行时；若镜像已存在，可：`SKIP_BUILD=1 ./ops/scripts/k8s-up.sh`
- 部署使用 **`kubectl kustomize … --load-restrictor LoadRestrictionsNone | kubectl apply -f -`**，用于加载 `platform/` 下配置（勿单独使用不带该参数的 `kubectl apply -k`，会报路径安全限制）。

## 一键下架

```bash
./ops/scripts/k8s-down.sh
```

会删除整个 **`monitoring-stack`** 命名空间（含 PVC 数据，请谨慎）。

## 本机 NodePort（宿主机 IP）

| 组件 | 端口 |
|------|------|
| ml-api | 30500 |
| Prometheus | 动态分配（脚本输出为准） |
| Grafana | 30300（默认 `admin` / `admin`） |
| Alertmanager | 30093 |
| Kibana | 30560 |

示例：

```bash
curl -s http://127.0.0.1:30500/health
```

## 与新目录结构的关系

- **`apps/ml-api/Dockerfile`**：用于构建 **`ml-api:dev`**（`k8s-up.sh` 引用该路径）。
- Kustomize 主入口：**`deployments/kustomize/`**。

## 说明

- Prometheus 在集群内通过 **`kubernetes_sd_configs`** 抓取 `monitoring-stack` 命名空间、标签 **`app=ml-api`** 的 Pod（与 Pod 上 **`prometheus.io/*`** 注解一致）。
- Logstash 使用 **`platform/logging/logstash/pipeline-k8s.conf`**（最小 Beats→ES 流水线）。
