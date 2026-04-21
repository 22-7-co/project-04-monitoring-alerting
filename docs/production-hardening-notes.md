# 生产加固说明（本仓库 vs 生产建议）

本文件描述**学习/演示栈**与**生产环境**之间的典型差距。不要求在本仓库全部落地实现；面试或上生产前可据此做检查清单。

---

## 身份与密钥

- **本仓库现状**：Grafana、Kibana 等使用默认或明文写在清单/文档中的凭据（如 `admin` / `admin`），便于本地实验。
- **生产建议**：所有人类凭据走 **Secret**（或 External Secrets / Vault）；默认账号禁用或强密码；定期轮换。
- **本仓库是否实施**：否（仅限本地/实验；见 [production-simulation.md](production-simulation.md)）。

---

## 网络暴露面

- **本仓库现状**：多组件使用 **NodePort** 暴露在节点 IP 上；无 Ingress、无 TLS 终止。
- **生产建议**：经 **Ingress + TLS**（或云 LB）对外；集群内部服务 ClusterIP；管理面走 VPN 或私有网络。
- **本仓库是否实施**：否。

---

## 传输加密

- **本仓库现状**：组件间 HTTP 明文（Prometheus、Grafana 数据源、Alertmanager、ES 等）。
- **生产建议**：对跨信任域流量使用 TLS；服务网格或 Sidecar 统一 mTLS（视团队标准）。
- **本仓库是否实施**：否。

---

## Kubernetes RBAC 与 ServiceAccount

- **本仓库现状**：Prometheus 使用专用 SA（见 `rbac-prometheus.yaml`）；其余组件多为默认 SA。
- **生产建议**：每个工作负载独立 SA；**最小 RBAC**；定期审计 `ClusterRoleBinding`。
- **本仓库是否实施**：部分（Prometheus）；其余未收紧。

---

## NetworkPolicy

- **本仓库现状**：未配置 NetworkPolicy，Pod 间默认可达。
- **生产建议**：按「需知」原则限制入口/出口（监控抓取、日志出口、DNS 等白名单）。
- **本仓库是否实施**：否。

---

## 供应链与镜像

- **本仓库现状**：镜像使用 **tag**（如 `grafana/grafana:10.2.2`、`prom/prometheus:v2.47.2`）。
- **生产建议**：关键镜像 pin **digest**；漏洞扫描（Trivy 等）；私有镜像仓库与拉取凭据。
- **本仓库是否实施**：否。

---

## 审计与合规（占位）

- **生产建议**：K8s Audit 日志、应用审计字段、保留策略与可检索性；按行业要求做数据驻留与脱敏。
- **本仓库是否实施**：未涉及。

---

## 上生产时建议优先做的三步

1. **换掉所有默认密码**，并改为 Secret 注入。  
2. **收敛暴露面**（Ingress + TLS，或仅内网 NodePort）。  
3. **为 Prometheus / ES 等状态组件定义备份与 RPO**（见 [operations-assumptions.md](operations-assumptions.md)）。
