# TradingCoach 产品化路线图 - 2026-05-22

> 背景：当前产品已经有可用的数据清洗、统计、持仓详情、AI Coach fallback 和回归测试基础。下一阶段重点不是继续堆页面，而是降低真实用户导入成本，并让分析结果更像“交易教练”，而不是“交易报表”。

## 1. 产品化北极星

TradingCoach 应该回答三个问题：

1. 我最近的交易到底哪里在赚钱、哪里在亏钱？
2. 哪些亏损是策略问题，哪些是执行问题，哪些只是市场环境问题？
3. 下一周我应该训练什么，才能减少同类错误？

现在产品更接近第一个问题，第二和第三个问题还偏薄。

## 2. 数据导入路线

### 2.1 短期：把文件导入做到稳定

目标：不接券商 API 之前，先让真实用户的 CSV/xlsx 导入不痛苦。

| 任务 | 说明 | 验收 |
|------|------|------|
| 导入向导 | 用户选择券商/模板，系统展示需要的字段 | 至少支持 IBKR、Futu、Tiger、Tradier/Alpaca、通用 CSV |
| 字段映射 UI | 用户可以把 `成交时间`、`Symbol`、`Qty`、`Commission` 映射到内部 schema | 映射可保存，下次自动套用 |
| 导入预检 | 导入前显示缺失字段、重复记录、币种、期权腿识别结果 | 不允许静默吞掉异常行 |
| 增量导入 | 识别已导入成交，避免重复计算 | 同一文件重复导入不会改变统计 |
| 错误报告 | 每个失败行给出修复建议 | 用户能下载错误行或在 UI 中修正 |

这是 P0，因为 API 直连也需要同一套标准化 schema。

### 2.2 中期：只读 broker connection

先做只读，不做下单。目标是让用户授权后同步 holdings、transactions、orders/fills，用于复盘。

| 方案 | 适用 | 优点 | 风险 |
|------|------|------|------|
| Aggregator：SnapTrade | 多券商覆盖、想快速连用户现有账户 | 文档显示连接后会同步账号，并可访问 account data；官网强调覆盖多家券商和股票/ETF/crypto/options 交易能力 | 成本、覆盖地区、合规、数据延迟需要商务确认 |
| Aggregator：Plaid Investments | 美国/加拿大投资账户，只读 holdings/transactions | 官方文档说明 Investments 可获取投资账户 holdings、securities、transactions | 不是交易执行 API；刷新和机构支持不是全覆盖 |
| Direct：IBKR Web API | 专业用户、IBKR 账户 | IBKR 正在统一 Web API，OAuth 2.0 是方向；适合长期深度集成 | 授权、会话、Flex/reporting、期权腿和历史成交口径复杂 |
| Direct：Futu OpenAPI | 港美股/期权用户，富途生态 | 官方 trade overview 暴露 account、funds、positions、orders、historical orders、fills、push | 需要本地 OpenD/权限；地区和账户资格限制 |
| Direct：Tiger Open API | Tiger 用户 | 官方说明 Open API SDK 支持行情、交易和 push，语言覆盖较全 | 地区、账户资金门槛、API 权限与历史数据完整性需验证 |
| Direct：Tradier/Alpaca | API-first 美股/期权用户 | Tradier 账户 API 包含 balances、positions、orders、history、gain/loss；Alpaca 有 activity stream 适合同步成交事件 | 用户覆盖不一定是当前目标客群；部分能力更偏开发者 |

建议优先级：

1. 先实现 broker adapter 抽象和 read-only sync pipeline。
2. 第一条真实集成优先选用户自己最常用的券商。如果目标用户是你自己，优先 IBKR/Futu/Tiger；如果面向美国开发者，优先 Alpaca/Tradier；如果面向多券商普通用户，评估 SnapTrade/Plaid。
3. 下单/自动交易能力全部推迟，默认只读。

### 2.3 长期：交易工具生态

只读同步稳定后，再考虑：

- 浏览器插件或本地 agent：从券商网页/桌面导出中辅助获取报表，但必须明确隐私边界。
- Webhook / scheduled sync：每天盘后自动同步并生成复盘。
- Broker health dashboard：展示连接状态、上次同步、缺失成交、重复成交、币种缺口。
- 多账户合并：账户维度、策略维度、币种维度分开，不把所有收益粗暴相加。

## 3. 分析能力路线

### 3.1 从“报表”升级为“诊断”

当前统计能看 P&L、胜率、评分、持仓列表，但还需要把交易问题拆成原因。

| 模块 | 要回答的问题 | 核心指标 |
|------|--------------|----------|
| Playbook / 策略归因 | 哪些策略真的有正期望？ | expectancy、profit factor、sample size、regime split |
| 执行质量 | 是计划错，还是执行差？ | entry slippage、exit slippage、planned vs actual、partial fill quality |
| 风险和仓位 | 亏损来自方向判断还是 sizing？ | risk per trade、R-multiple、max adverse excursion、position concentration |
| 退出纪律 | 赚钱单是否拿不住，亏损单是否拖太久？ | MFE/MAE、giveback、time-to-exit、stop violation |
| 期权专项 | 期权腿、价差、希腊字母和到期风险是否合理？ | spread P&L、theta decay、delta exposure、DTE bucket |
| 市场环境 | 错误是否集中在特定 regime？ | VIX、指数趋势、板块强弱、财报/事件窗口 |
| 行为复盘 | 哪些错误重复出现？ | revenge trade、oversizing、early exit、late chase、rule violation tags |

### 3.2 让 AI Coach 有“教练动作”

AI Coach 不应只是解释图表。更有价值的动作：

1. 每日复盘队列：自动挑出最值得复盘的 5 笔交易。
2. 错误聚类：把亏损按“策略不适配、入场追高、止损拖延、仓位过大、事件风险”等聚类。
3. 训练任务：根据最近 20 笔交易生成一条训练目标，例如“下周只训练减小亏损单持仓时间”。
4. 反事实分析：如果按计划止损/止盈，P&L 会怎样变化。
5. 证据链输出：每个建议都引用具体交易、指标和缺失数据，不给空泛建议。

### 3.3 让用户更容易信任分析

| 痛点 | 产品解法 |
|------|----------|
| 评分里有 `?`，用户不知道为什么 | 每个 `?` 展示缺失数据：缺 stop、缺入场计划、缺 market regime、缺手续费等 |
| 指标多但行动少 | 每个页面加“下一步动作”：补数据、复盘、标记策略、调整规则 |
| 导入后不知道数据是否可靠 | 导入完成后给 data quality score 和异常清单 |
| 复盘成本太高 | 给 review queue，按损失、异常、重复错误排序 |
| 多币种误读 | 所有聚合指标显示 base currency 和 FX 日期；支持 currency breakdown |

## 4. 近期任务建议

### P0：数据导入可信

- 设计统一 trade/fill/position/cash schema。
- 做导入预检和字段映射 UI。
- 支持重复检测和增量导入。
- 给每次导入生成 data quality report。

2026-05-22 进展：已先落地后端只读导入预检切片，`POST /api/v1/upload/trades/preview` 会识别券商格式、返回 broker、置信度、总行数、已成交行数、跳过行数、列名、错误和警告，不写数据库。下一步再把这个能力接到 Landing/Upload UI。

### P1：分析深度

- 做 playbook/strategy tagging。
- 增加 R-multiple、MFE/MAE、giveback、持仓时间分布。
- 增加“亏损原因聚类”和“最值得复盘交易”。
- 为 `?` 评分补齐缺失原因解释。

### P1：Broker connection 技术预研

- 做 `BrokerAdapter` interface：`connect`、`sync_accounts`、`sync_transactions`、`sync_positions`、`sync_orders`、`sync_fills`。
- 先实现 read-only mock adapter，用 fixtures 跑完整同步。
- 选择 1 个真实券商做 spike，不要同时开多个。
- 加 OAuth/token 存储、撤销连接、同步日志、隐私模式验收。

### P2：产品体验

- 做 onboarding checklist。
- 做每周复盘报告。
- 做用户可编辑的交易标签和笔记。
- 做分析结果导出为 Markdown/PDF。

## 5. 参考资料

- [IBKR Web API Documentation](https://www.interactivebrokers.com/campus/ibkr-api-page/webapi-doc/)
- [SnapTrade Getting Started](https://docs.snaptrade.com/docs/getting-started)
- [SnapTrade broker connectivity overview](https://snaptrade.com/)
- [Plaid Investments overview](https://plaid.com/docs/investments/)
- [Plaid Investments API reference](https://plaid.com/docs/api/products/investments/)
- [Futu OpenAPI trade overview](https://openapi.futunn.com/futu-api-doc/en/trade/overview.html)
- [Tiger Open Platform introduction](https://docs-en.itigerup.com/docs/intro)
- [Tradier Account API](https://docs.tradier.com/docs/account-details)
- [Tradier Trading API](https://docs.tradier.com/docs/trading)
- [Alpaca Activity SSE](https://docs.alpaca.markets/us/docs/activity-sse)
