# 监控告警项目：企业向完善计划

本文对应此前讨论的「面试向交付」缺口，按优先级分阶段执行。第 7 点（面试叙事）的落地材料在目录 [`interview-orals/`](interview-orals/)。

---

## 阶段划分与成功标准

### 第 1 点：文档与需求对齐现实

| 动作 | 成功标准 |
|------|----------|
| 在 `requirements.md` 文首增加「实现形态说明」：当前以 K8s + Kustomize 为准，Compose 相关条目为历史/可选 | 新人读 2 分钟内知道以哪份文档验收 |
| 新增一页 `docs/requirements-matrix.md`（或等价小节）：FR 编号 → 实现位置（路径/组件）→ 状态（已实现/部分/未做）→ 备注 | 任意一条需求可追溯到仓库内具体产物 |
| README 增加指向矩阵与 `production-simulation.md` 的链接 | 单入口可导航到全部权威说明 |

**优先级**：P0（成本低、面试官第一印象）

---

### 第 2 点：可重复的「证明它可用」

| 动作 | 成功标准 |
|------|----------|
| CI（GitHub Actions / 其他）跑：`pytest`（现有测试）、`kubectl kustomize deployments/kustomize` 成功 | 无集群时也能拦住明显配置回归 |
| 可选：`shellcheck` 对 `ops/scripts/*.sh` | 脚本修改有静态检查 |
| 文档写明：本地全量验证需 k3s 等前提 + 一条推荐命令序列 | 与 CI 能力边界一致，避免过度承诺 |

**优先级**：P0～P1

---

### 第 3 点：告警与 on-call 闭环

| 动作 | 成功标准 |
|------|----------|
| 从现有 `alerts.yml` 中选 2～3 条规则，各写半页到一页 Runbook：`触发含义` → `先看哪张图/哪条查询` → `常见根因` → `缓解步骤` → `如何宣布恢复` | 非作者也能按文档操作一轮 |
| 任选一种通知落地（Webhook 打到一个可调试的 HTTP 服务、或文档级「若接 Slack/企微则…」+ 配置片段） | 能说清告警从 Prometheus 到人的路径 |

**优先级**：P1

---

### 第 4 点：安全与多租户意识（文档优先）

| 动作 | 成功标准 |
|------|----------|
| 在 `docs/` 增加 `production-hardening-notes.md`：Secret、Grafana RBAC、Ingress+TLS、NetworkPolicy、镜像 tag 策略、默认密码替换 | 明确「学习栈 vs 生产」边界，不要求本仓库全部实现 |
| README 或上架文档中一句：默认凭据仅用于本地/实验 | 降低「不知道风险」的印象 |

**优先级**：P1（以文档为主时工作量可控）

---

### 第 5 点：可观测性深度（选做轨道）

任选 **一条** 做深即可在面试中当「亮点」：

| 轨道 | 动作 | 成功标准 |
|------|------|----------|
| A. Tracing | 最小接入 OTel + 一个后端（如 Jaeger）或文档化「与现有指标如何关联」 | 能说清从 trace id 到日志/指标的排障路径 |
| B. SLO | 一条 SLI（如可用性或延迟）+ Grafana 上一个 error budget / burn 相关面板 + 与现有告警的关系 | 能口述 SLO 与告警的区别 |

**优先级**：P2（时间充裕再做）

---

### 第 6 点：可靠性与运维细节

| 动作 | 成功标准 |
|------|----------|
| 在 `production-simulation.md` 或独立小节写清：资源 request/limit 策略、是否 HPA/PDB、单机实验为何简化 | 被问到「为什么没上 HPA」有答案 |
| 数据保留：Prometheus / ES 的保留与「可接受丢失」假设一句 | 体现备份与 RPO 意识 |

**优先级**：P1～P2

---

### 第 7 点：个人叙事与面试口述

**不放在本计划正文展开**，统一放在目录 **[`interview-orals/`](interview-orals/)**：

- [`interview-orals/questions-and-oral-answers.md`](interview-orals/questions-and-oral-answers.md)：项目相关高频面试题 + 建议口述要点（可背改用自己的话）。
- [`interview-orals/star-case.md`](interview-orals/star-case.md)：STAR 排障案例，与 [`requirements-matrix.md`](requirements-matrix.md) 中 FR 对照。

**执行方式**：随项目演进每季度扫一遍 Q&A，把新踩的坑（如 DNS、告警模板、存储类）补进「根因类」题目。

**优先级**：P0（与投递/面试同步维护）

---

## 建议执行顺序（时间紧时）

1. 第 7 点材料（半天）：保证面试有话术。  
2. 第 1 点 + 第 2 点 CI（各约半天～1 天）。  
3. 第 3 点 Runbook（1～2 天）。  
4. 第 4、6 点以文档补齐（并行，约 1 天）。  
5. 第 5 点按兴趣选一条深挖。

---

## 跟踪方式（可选）

在 issue 或私有看板中为每条 FR 矩阵行建任务；合并 PR 时更新矩阵中的「状态」列，避免文档与代码再次分叉。
