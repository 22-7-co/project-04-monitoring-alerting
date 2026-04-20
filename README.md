# project-04-monitoring-alerting

这个仓库只保留 **k8s 全栈监控方案**（不再包含 compose 方案）。

## 当前架构

- 应用：`ml-api`（3 副本）
- 监控：Prometheus / Alertmanager / Grafana / Node Exporter
- 日志：Elasticsearch / Logstash / Kibana / Filebeat
- 命名空间：`monitoring-stack`

## 目录

- `apps/ml-api/`：应用镜像构建
- `platform/observability/`：Prometheus、Grafana、Alertmanager 配置
- `platform/logging/`：Logstash、Filebeat 配置
- `deployments/kustomize/`：Kubernetes 资源清单
- `ops/scripts/`：一键上架/下架脚本
- `docs/production-simulation.md`：部署与排障说明

## 一键上架

```bash
./ops/scripts/k8s-up.sh
```

跳过镜像构建：

```bash
SKIP_BUILD=1 ./ops/scripts/k8s-up.sh
```

## 一键下架

```bash
./ops/scripts/k8s-down.sh
```

## 宿主机访问

`k8s-up.sh` 会打印实时 NodePort（Prometheus 可能因冲突自动分配新端口）。

常见固定端口：

- ml-api: `30500`
- grafana: `30300`
- alertmanager: `30093`
- kibana: `30560`
- prometheus: 可能动态分配（看脚本输出）

快速检查：

```bash
kubectl -n monitoring-stack get svc
curl -s http://127.0.0.1:30500/health
```

