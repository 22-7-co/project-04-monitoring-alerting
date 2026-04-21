# 本项目面试：常见问题与口述要点

使用方式：不必照背，用要点串成自己的 30 秒～2 分钟版本。数字与命令以你当前环境为准，面试前用 `kubectl get` 核对一遍。

**结构化案例（STAR）**：[star-case.md](star-case.md)（与 [requirements-matrix.md](../requirements-matrix.md) 中 FR-1.1 / FR-2.1 对照）。**需求与实现矩阵**：[requirements-matrix.md](../requirements-matrix.md)。

---

## 一、项目定位与范围（开场）

### Q1：用一两分钟介绍一下这个项目。

**口述要点**

- 目标：在 Kubernetes 上搭一套**可运行的监控与日志栈**，服务一个示例应用 `ml-api`（多副本）。
- 指标侧：Prometheus 服务发现抓 Pod、`Grafana` 预置数据源与大盘、`Alertmanager` 接告警路由。
- 日志侧：Filebeat → Logstash → Elasticsearch → Kibana，与指标形成「指标 + 日志」双通道排障。
- 交付物：Kustomize 清单、一键上下架脚本、流量模拟脚本、指标相关单元测试。
- 明确边界：偏**学习与演示**，生产级加固写在文档假设里，未全部实现。

---

## 二、架构与选型

### Q2：为什么用 Kustomize 而不是 Helm？

**口述要点**

- 清单量适中，**无模板逻辑**时 Kustomize 更直观，diff 友好，适合教学与代码审阅。
- 若团队统一 Helm，可说明：当前结构可迁到 Chart，**组件边界已按目录拆开**（`deployments/kustomize` vs `platform/`）。

### Q3：Prometheus 怎么发现 `ml-api`？

**口述要点**

- 使用 **Kubernetes SD**，在配置里限定命名空间与标签；Pod 上带 **prometheus.io/scrape、port、path** 注解，与 `ml-api` Deployment 一致。
- 新 Pod 起来后会在发现周期内自动出现在 target 里；缩容下线后目标消失，**无需改 Prometheus 静态配置**。

### Q4：Grafana 的数据源为什么写 `http://prometheus:9090`？

**口述要点**

- 集群内走 **Service DNS**，与 Pod 同命名空间时短名 `prometheus` 即可。
- 若遇连接异常，会查 **Endpoints / `nslookup` / 从本 Pod curl Service IP**，排除 DNS 或上游代理劫持（例如错误解析到非集群网段）。

---

## 三、排障与真实坑（高频加分）

### Q5：你遇到过最难的问题是什么？怎么定位的？

**口述要点（可替换为你真实案例）**

- **现象**：Grafana 报数据源错误，例如对 `query_range` 的请求 **EOF** 或 500。
- **假设**：Grafana 到 Prometheus 的网络或 **DNS 解析** 异常，而非应用代码。
- **验证**：在 Grafana Pod 内 `curl`/`nslookup` **Service 名**与 **ClusterIP**；若名字解析到异常网段（如 `198.18.x.x`），而 ClusterIP 访问正常，则锁定为 **DNS 被宿主机或代理污染**（与某些 TUN/Fake-IP 场景一致）。
- **处理**：关闭或绕过干扰代理、或修正 CoreDNS/上游；临时可用 ClusterIP 验证路径。
- **收获**：区分「应用挂了」与「解析/流量路径错了」，**先分层验证**。

完整 STAR 写法见 [star-case.md](star-case.md)；口述时对应矩阵 **FR-2.1 / FR-1.1** 的验证方式列。

### Q6：Prometheus 或 Alertmanager 日志里出现 EOF 说明什么？

**口述要点**

- 通常表示 **TCP 已连上但对端未完整返回 HTTP 体就断开**，常见于对端重启、被 OOM、中间设备断开、或连到了非 HTTP 服务。
- 排查顺序：对端 Pod 是否 **Ready / 重启**、Service Endpoints 是否指向正确、同命名空间 **直连 Pod IP** 与 **经 Service** 对比。

---

## 四、告警与 SLO

### Q7：告警规则怎么组织？如何避免「告警风暴」？

**口述要点**

- 规则集中在仓库的 Prometheus rules 文件中，按**业务域或组件**分 group。
- 缓解：合理 **for** 持续时间、`group_wait`/`group_interval`/`repeat_interval`（Alertmanager）、同类告警合并、优先 **SLO/用户影响** 类信号而非每一跳中间件都 paging。

### Q8：SLO 和「CPU 高」这类告警有什么区别？

**口述要点**

- **SLO** 描述对用户承诺的服务水平（可用性、延迟等），error budget 花完才需要严肃升级。
- **CPU 高** 多为容量或噪声，未必立刻影响用户；应把**用户感知**和**资源指标**分层，避免把运维指标全部升级成紧急页。

---

## 五、安全与生产边界

### Q9：这套直接上生产有什么问题？

**口述要点**

- 默认账号、NodePort 暴露、无 TLS、无 NetworkPolicy、Secret 未与 Git 分离等。
- 生产上会：强认证、RBAC、Ingress + TLS、最小权限 ServiceAccount、镜像固定 digest、备份与保留策略、审计与配额。

### Q10：密钥怎么管理？

**口述要点**

- 仓库内不落真实密钥；本地用 **Secret** 或 sealed-secrets/external-secrets 等（按平台选），CI 用 **vault / OIDC** 注入。
- 本学习项目可用 `env` + `.gitignore`，面试时说明**梯度**即可。

---

## 六、可观测性与日志

### Q11：有指标了为什么还要 ELK？

**口述要点**

- 指标适合**聚合、趋势、告警**；日志适合**上下文、单次请求、栈与业务字段**。
- 排障典型路径：告警/大盘发现异常时间窗 → **PromQL 缩小范围** → **Kibana 按时间/trace id/request id 钻日志**。

### Q12：如果只能加一项，你会加 tracing 还是加更多面板？

**口述要点**

- 优先 **分布式追踪**（或至少 trace id 贯通日志），因为跨服务延迟与调用链问题用纯指标+日志成本更高；面板在指标完备后按需长。

---

## 七、可靠性与成本

### Q13：Prometheus 数据丢了怎么办？

**口述要点**

- 先声明 **RPO/RTO** 假设：学习栈可接受丢近期数据；生产用 **持久卷、快照、remote write 到长期存储** 等组合。
- 说明 retention 与磁盘监控，避免 TSDB 写满导致整体不可用。

### Q14：为什么 ml-api 是 3 副本？Prometheus 是单副本？

**口述要点**

- API 多副本演示**负载与滚动更新**；Prometheus HA 涉及**联邦或 Thanos/Mimir** 等，超出当前范围，单实例与 PVC 足够演示抓取与查询；面试中承认取舍即可。

---

## 八、协作与工程化

### Q15：怎么保证别人能复现你的环境？

**口述要点**

- README + `production-simulation.md` 写清**前置**（k8s 版本、StorageClass、端口说明）。
- CI 跑 **kustomize build + 测试**，全栈联调依赖集群时在文档标明，避免「只有本机行」。

### Q16：如果需求文档和实现不一致你怎么处理？

**口述要点**

- **以可运行系统 + [requirements-matrix.md](../requirements-matrix.md) 为准**：每条 FR 有实现路径、状态与验证命令；`requirements.md` 文首已说明 Compose 等为课程原文表述。
- 新需求或改监控行为：**先改代码/清单，再更新矩阵对应行**，避免口头传说。

---

## 九、收尾反问（可选）

面试结束前可问面试官（择一）：

- 贵司监控栈是 **自托管 Prometheus 系** 还是 **云厂商托管**？告警是否统一经 On-Call 平台？
- SLO 目前是**平台团队**统一还是**业务团队**各自认领？

---

## 十、自备 3 分钟「故事线」提纲（口述用）

1. **背景**：为什么做监控告警项目，要解决什么问题。  
2. **架构**：三条线——采集与存储、可视化与告警、日志链路。  
3. **难点**：选一个真实坑（DNS、存储类、告警模板、资源不足等）讲清现象→验证→根因→修复；可与 [star-case.md](star-case.md) 及 [requirements-matrix.md](../requirements-matrix.md) 中相关 FR 对齐。  
4. **验证**：流量模拟、`pytest`、CI（`.github/workflows/ci.yml`）、或一次手工上架演练。  
5. **若上生产**：两句话交代 [production-hardening-notes.md](../production-hardening-notes.md) 与 [operations-assumptions.md](../operations-assumptions.md) 中的边界。

将第 3 点与 [`../production-simulation.md`](../production-simulation.md) 及 Runbook（[`../runbooks/`](../runbooks/)）对齐，避免面试时说漏或与仓库不一致。

---

## 维护提示（根因类题目）

每次调整 **Prometheus 规则、Alertmanager、Grafana 数据源或上架脚本** 后，检查 **Q5/Q6** 与 [star-case.md](star-case.md) 是否仍准确；若有新坑，补一条「现象 → 命令 → 根因」到本节或独立案例文件。
