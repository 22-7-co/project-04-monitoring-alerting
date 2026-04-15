# 项目 04：监控与告警系统

---

## 项目概览

构建一个面向 ML 基础设施的完整监控与告警系统，覆盖应用指标、基础设施健康状态、模型性能和业务 KPI。本项目将引入生产级可观测性能力：日志、指标、追踪、告警与故障响应。

### 构建了什么

一个完整的可观测性技术栈，用于监控：
- **基础设施**：CPU、内存、磁盘、网络使用情况
- **应用**：请求速率、延迟、错误率
- **ML 模型**：每秒预测数、推理延迟、准确率、漂移
- **业务指标**：SLA、用户请求量、成功率

### 真实场景背景

你的 ML 系统现在已经上线（项目 1-3），但如果没有完善监控，就等于“盲飞”。当凌晨 3 点出现故障时，你需要第一时间知道；当模型发生漂移时，你需要收到告警；当基础设施压力上升时，你需要有可视化洞察。本项目模拟了搭建生产级可观测性系统的全过程。

### 学习产出

1. 部署监控基础设施（Prometheus、Grafana、ELK Stack）
2. 为应用接入指标、日志和追踪
3. 面向不同角色创建运维仪表盘
4. 实现用于主动发现故障的告警规则
5. 搭建日志聚合与分析流水线
6. 监控 ML 专属指标（漂移、数据质量、模型性能）
7. 编写值班 Runbook 以支持故障响应
8. 集成事件管理平台（PagerDuty、Opsgenie）

---

## 技术栈

| 组件 | 技术 | 用途 |
|-----------|------------|---------|
| **指标采集** | Prometheus 2.47+ | 时序指标存储 |
| **告警** | Alertmanager 0.26+ | 告警路由与通知 |
| **可视化** | Grafana 10.2+ | 仪表盘与可视化 |
| **日志存储** | Elasticsearch 8.11+ | 日志聚合与检索 |
| **日志处理** | Logstash 8.11+ | 日志解析与转发 |
| **日志可视化** | Kibana 8.11+ | 日志搜索与可视化 |
| **日志采集** | Filebeat 8.11+ | 从节点收集日志 |
| **指标导出器** | Node Exporter | 基础设施指标 |
| **应用埋点** | prometheus-client (Python) | 应用指标 |

---

## 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        监控系统架构                             │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                         数据源层                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Kubernetes  │  │ 应用服务     │  │ ML 模型     │             │
│  │ 集群         │  │ (API/Web)    │  │ (推理)      │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │ 指标            │ 指标 + 日志     │ 指标 + 日志        │
└─────────┼─────────────────┼─────────────────┼────────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                         采集层                                   │
│  ┌──────────────────────────┐    ┌─────────────────────────┐    │
│  │      Prometheus          │    │   Filebeat/Fluentd      │    │
│  │  - 抓取指标               │    │   - 采集日志            │    │
│  │  - 存储时序数据           │    │   - 发送到 Logstash     │    │
│  │  - 评估告警规则           │    │                         │    │
│  └────────┬─────────────────┘    └───────────┬─────────────┘    │
└───────────┼───────────────────────────────────┼──────────────────┘
            │                                   │
            ▼                                   ▼
┌──────────────────────────┐      ┌────────────────────────────┐
│     Alertmanager         │      │      Logstash              │
│  - 告警路由               │      │  - 解析日志               │
│  - 去重                   │      │  - 转换与增强             │
│  - 发送通知               │      │  - 转发到 ES              │
└────────┬─────────────────┘      └──────────┬─────────────────┘
         │                                   │
         │                                   ▼
         │                        ┌────────────────────────────┐
         │                        │    Elasticsearch           │
         │                        │  - 存储日志               │
         │                        │  - 索引与检索             │
         │                        └──────────┬─────────────────┘
         │                                   │
         ▼                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                         可视化层                                 │
│  ┌──────────────────────┐         ┌──────────────────────┐      │
│  │      Grafana         │         │       Kibana         │      │
│  │  - 仪表盘             │         │  - 日志搜索          │      │
│  │  - 指标可视化         │         │  - 日志分析          │      │
│  └──────────────────────┘         └──────────────────────┘      │
└──────────────────────────────────────────────────────────────────┘
            │                                   │
            ▼                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                         通知层                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  邮件     │  │  Slack   │  │PagerDuty │  │ Webhook  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└──────────────────────────────────────────────────────────────────┘
```

---

## 项目结构

```
project-04-monitoring-alerting/
├── README.md                          # 本文件
├── requirements.md                    # 详细需求与 SLI/SLO 说明
├── architecture.md                    # 可观测性架构说明
├── src/
│   ├── instrumentation.py            # Prometheus 指标埋点（STUB）
│   └── custom_metrics.py             # 自定义 ML 指标（STUB）
├── prometheus/
│   ├── prometheus.yml                # Prometheus 配置（STUB）
│   └── alerts.yml                    # 告警规则（STUB）
├── grafana/
│   ├── dashboards/
│   │   └── ml-overview.json         # ML 仪表盘模板
│   └── datasources.yml              # Grafana 数据源配置
├── elasticsearch/
│   ├── logstash.conf                # Logstash 流水线（STUB）
│   └── kibana-dashboard.ndjson      # Kibana 仪表盘导出文件
├── tests/
│   └── test_metrics.py              # 指标测试（STUB）
├── docker-compose.yml               # 完整监控栈
├── .env.example                     # 监控配置示例
└── docs/
    ├── SETUP.md                     # 部署说明
    ├── RUNBOOK.md                   # 值班 Runbook
    └── TROUBLESHOOTING.md           # 常见问题排查
```

---

## 快速开始

### 第 1 步：阅读需求

先阅读 `requirements.md`，重点理解：
- 功能需求（指标、仪表盘、告警、日志）
- 非功能需求（性能、可靠性、可扩展性）
- 成功标准

### 第 2 步：理解架构

阅读 `architecture.md`，重点理解：
- 监控栈组件
- 数据流（指标、日志、告警）
- 集成点

### 第 3 步：搭建基础设施

1. 将 `.env.example` 复制为 `.env` 并完成配置
2. 使用 Docker Compose 启动监控栈：
   ```bash
   docker-compose up -d
   ```
3. 验证所有服务是否正常运行：
   ```bash
   docker-compose ps
   ```

### 第 4 步：完善代码桩

按各个 stub 文件中的 TODO 逐步完成：

1. **src/instrumentation.py**：实现 Prometheus 指标
2. **src/custom_metrics.py**：添加 ML 专属指标
3. **prometheus/prometheus.yml**：配置抓取目标
4. **prometheus/alerts.yml**：定义告警规则
5. **elasticsearch/logstash.conf**：配置日志处理
6. **tests/test_metrics.py**：编写指标测试

### 第 5 步：创建仪表盘

1. 访问 Grafana：`http://localhost:3000`（admin/admin123）
2. 导入或创建仪表盘：
   - 基础设施仪表盘
   - 应用仪表盘
   - ML 模型仪表盘
   - 业务仪表盘
3. 将仪表盘 JSON 保存到 `grafana/dashboards/`

### 第 6 步：测试告警

1. 触发测试告警（模拟高 CPU、错误、漂移）
2. 验证告警是否正确触发
3. 检查告警是否路由到正确通知渠道
4. 在 runbook 中记录告警处理流程

### 第 7 步：完善文档

补全文档：
- `docs/SETUP.md`：搭建与部署指南
- `docs/RUNBOOK.md`：值班故障响应流程
- `docs/TROUBLESHOOTING.md`：常见问题与解决方案

---

## 核心概念

### 指标类型

1. **Counter**：单调递增值（总请求数、错误数）
2. **Gauge**：当前值（CPU 使用率、内存、活跃连接）
3. **Histogram**：数值分布（请求耗时、响应大小）
4. **Summary**：滑动时间窗口分位数（P50、P95、P99 延迟）

### 四大黄金信号（Four Golden Signals）

每个服务都应监控：

1. **延迟（Latency）**：请求处理耗时
2. **流量（Traffic）**：系统承载请求量
3. **错误（Errors）**：失败请求比例
4. **饱和度（Saturation）**：服务“接近满载”的程度

### 告警设计原则

- **可执行**：每条告警都应需要人工处理动作
- **有意义**：优先告警症状，而不是底层原因
- **有上下文**：携带足够信息以支持分诊
- **按严重级别分类**：Critical / Warning / Info
- **去重**：避免告警风暴

### SLI、SLO、SLA

- **SLI（Service Level Indicator）**：可度量指标（例如：99% 请求 < 200ms）
- **SLO（Service Level Objective）**：目标值（例如：99.9% 可用性）
- **SLA（Service Level Agreement）**：带违约责任的服务协议

---

## 交付清单

### 基础设施（必做）

- [ ] Prometheus 已部署并抓取指标
- [ ] Alertmanager 已配置路由规则
- [ ] Grafana 已配置所有数据源
- [ ] Elasticsearch 集群运行正常
- [ ] Logstash 正在处理日志
- [ ] Kibana 已配置索引模式
- [ ] Filebeat 正在发送日志

### 埋点与监控（必做）

- [ ] 应用指标已埋点（HTTP 请求、延迟、错误）
- [ ] ML 指标已埋点（预测、推理耗时、准确率）
- [ ] 已实现结构化 JSON 日志
- [ ] 已集成数据漂移检测
- [ ] 模型性能监控已启用

### 仪表盘（至少 4 个）

- [ ] 基础设施仪表盘（CPU、内存、磁盘、网络）
- [ ] 应用仪表盘（请求、错误、延迟）
- [ ] ML 模型仪表盘（预测、漂移、准确率）
- [ ] 业务仪表盘（SLA、成功率）

### 告警（至少 12 条）

基础设施：
- [ ] CPU 使用率过高
- [ ] 内存使用率过高
- [ ] 磁盘空间不足
- [ ] 服务不可用

应用：
- [ ] 错误率过高
- [ ] 延迟过高
- [ ] 吞吐过低
- [ ] 响应时间过长

ML 模型：
- [ ] 模型准确率下降
- [ ] 检测到数据漂移
- [ ] 推理延迟过高
- [ ] 预测置信度过低

### 文档（必做）

- [ ] 搭建说明（SETUP.md）
- [ ] 值班 Runbook（RUNBOOK.md）
- [ ] 故障排查指南（TROUBLESHOOTING.md）
- [ ] 架构图
- [ ] 告警响应流程

---

## 实现测试

### 指标测试

```bash
# 检查 Prometheus 是否已抓取目标
curl http://localhost:9090/api/v1/targets

# 查询一个指标
curl http://localhost:9090/api/v1/query?query=up

# 测试应用 metrics 端点
curl http://localhost:5000/metrics
```

### 告警测试

```bash
# 模拟高 CPU
stress-ng --cpu 8 --timeout 60s

# 触发错误率告警
for i in {1..100}; do curl http://localhost:5000/error; done

# 查看当前活跃告警
curl http://localhost:9090/api/v1/alerts
```

### 日志测试

```bash
# 发送测试日志
echo '{"level": "error", "message": "Test error"}' | \
  curl -X POST -H "Content-Type: application/json" \
  -d @- http://localhost:5000/

# 在 Elasticsearch 中搜索日志
curl http://localhost:9200/_search?q=level:error
```

---

## 常见陷阱

1. **告警疲劳**：噪声告警太多，团队逐渐忽略
   - **解决方案**：先从关键告警开始，再逐步调优阈值

2. **未做告警测试**：真正故障时告警不触发
   - **解决方案**：上线前模拟故障并验证告警链路

3. **仪表盘设计不佳**：信息过载、可视化不清晰
   - **解决方案**：按受众拆分仪表盘，每个仪表盘目标明确

4. **上下文缺失**：告警信息不足，无法快速分诊
   - **解决方案**：补充关键标签、注释与 runbook 链接

5. **无保留策略**：存储空间被耗尽
   - **解决方案**：配置保留周期（指标 30 天、日志 90 天）

6. **忽略 ML 指标**：只监控基础设施，不看模型健康
   - **解决方案**：监控模型性能、漂移和数据质量

---

## 评估标准

你的项目将按以下维度评分：

1. **指标采集（20%）**：埋点是否全面
2. **可视化（20%）**：仪表盘是否专业且实用
3. **告警（20%）**：告警是否可执行且阈值合理
4. **日志（15%）**：日志是否结构化、可检索、有价值
5. **ML 监控（15%）**：漂移检测与性能跟踪是否完整
6. **文档（10%）**：runbook 与操作文档是否完整

**及格分数**：70/100

---

## 参考资源

### 官方文档

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Elasticsearch Documentation](https://www.elastic.co/guide/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)

### 教程

- [Prometheus Getting Started](https://prometheus.io/docs/prometheus/latest/getting_started/)
- [Grafana Fundamentals](https://grafana.com/tutorials/grafana-fundamentals/)
- [ELK Stack Tutorial](https://www.elastic.co/guide/en/elastic-stack-get-started/current/get-started-elastic-stack.html)

### 最佳实践

- [Google SRE Book - Monitoring](https://sre.google/sre-book/monitoring-distributed-systems/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Grafana Best Practices](https://grafana.com/docs/grafana/latest/best-practices/)

---

## 下一步建议

完成本项目后：

1. **作品集**：录制演示视频，展示实时监控与告警能力
2. **简历**：加入“生产级监控与可观测性”技能
3. **持续学习**：进入项目 5（生产就绪 ML 系统 - Capstone）
4. **进阶方向**：
   - 分布式追踪（Jaeger、Tempo）
   - APM（应用性能监控）
   - 成本监控与优化
   - 自动化故障修复

---

**项目版本**：1.0
**最后更新**：2025 年 10 月
**维护团队**：AI Infrastructure Curriculum Team
**联系方式**：ai-infra-curriculum@joshua-ferguson.com
# Project 04: Monitoring & Alerting System

---