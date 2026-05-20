# TradingCoach 交易复盘全景研究与 Feature 路线图

> 一旦本文件所属内容有变化，请同步更新 `project_docs/readme.md` 索引。
>
> **生成时间**: 2026-05-20
> **研究范围**: 25 篇方法论文章、12 位复盘 KOL、39 位投资大师语录、14 款同类产品 landscape
> **目的**: 为 TradingCoach 后续 6 个月的复盘能力建设提供研究底座 + 可落地 Feature 列表

---

## 0. 执行摘要 (TL;DR)

**核心结论**：交易复盘的本质不是"记录"，而是"在结果到来前就把过程钉死，以便事后能区分『决策好坏』和『盈亏好坏』。" 中英文社区在这一点上殊途同归（孟岩 = Annie Duke = Howard Marks = 段永平）。

**TradingCoach 的差异化窗口**（来自 14 款产品 landscape）：
1. **反事实回测** — Edgewonk 有 alt-strategy 模拟，但没人做"如果你执行了止损，整年亏损削减 X%"这种基于真实交易的 counterfactual。TradingCoach 现有 cf1-cf5 引擎已经独占。
2. **中英双语 + 港美股混合 + Futu/IBKR 原生** — Tradervue/Tradezella 英文 only；同花顺/复盘盒子 A 股 only。港美股+港股+期权混合账户在主流工具里完全空白。
3. **行为锚定 AI 教练** — TraderSync 的 Cypher 给的是泛泛"你周二表现更好"。基于用户自己的 8 维评分 + counterfactual delta 才能说"你在 7 笔 NVDA 财报交易里平均提前 12 分钟离场，损失 $4,300"。
4. **期权价差 + 隐私模式截图分享** — 只有 TradingDiary Pro / Trademetria 处理 spread P&L 还做得难看；没人提供"打码账户大小+股票代码"的安全分享，这是 viral 钩子。

**Top 5 建议 Feature**（ROI/Effort 排序，详见第 6 节）：
1. 决策日志 (Decision Journal) — 开仓时强制 2 句话 thesis + 卖出触发条件
2. 过程分/结果分双轴展示 — 当前 V2 评分已有数据，UI 拆分即可
3. 周度复盘模板 (Weekly Retro Loop) — 仿 Steenbarger/Bellafiore，强制输出"明天要练的一个动作"
4. 错误分类二分（违纪 vs 概率）— 段永平不为清单思想 + Pabrai 错误清单
5. 年度致股东信自动生成 — 中文圈仪式感，刘建位/唐朝/孟岩共识

---

## 1. 方法论文献库（25 条，CN 11 + EN 14）

### 1.1 中文社区（11 条）

| # | 标题 | 作者/来源 | 方法论核心 | TradingCoach 借鉴点 |
|---|------|----------|-----------|------------------|
| C1 | [我的投资体系：复盘三件事](https://xueqiu.com/1494750910) | 邱国鹭，雪球 | 每周三问：买入逻辑是否仍成立 / 估值是否仍合理 / 有无更好替代 | 持仓页加"逻辑是否仍成立"周复核 checkbox |
| C2 | [大道无形我有型：不为清单](https://xueqiu.com/6246718469) | 段永平，雪球 | 先列"不做什么清单"再复盘；错误分两类：本可避免 vs 不可避免 | 错误分类引入"违纪"vs"概率事件"二分 |
| C3 | 唐书房：手把手教你写交易日记 | 老唐，微信公众号 | 每笔记录"买入理由+预期持有时长+卖出触发条件"，三年后回看打分 | 开仓时强制填写"卖出触发条件"字段 |
| C4 | [孟岩：决策质量 vs 结果质量](https://youzhiyouxing.cn) | 孟岩，有知有行 | 复盘分两轴：决策质量 + 结果质量，赚钱的烂决策也算错 | 8 维评分里过程分与盈亏分解耦展示 |
| C5 | [如何写交易日记？](https://www.zhihu.com/question/27983890) | 路过銀河，知乎 | 日记四栏：情绪/决策/复盘/改进；情绪与亏损相关性周聚合 | 加情绪标签字段（FOMO/恐惧/贪婪/平静） |
| C6 | 林园投资逻辑复盘 | 林园，雪球专栏 | 只复盘消费医药赛道，建"长期赛道清单"，赛道外交易一律标违规 | 用户自定义白名单赛道，赛道外标红 |
| C7 | 但斌《时间的玫瑰》第三章 | 但斌 | 长期持有≠不复盘，每季度做"假如今天没买还会买吗"测试 | 季度自动推送"重置买入"模拟问卷 |
| C8 | 张磊《价值》第六章 | 张磊 | 复盘聚焦"是否找到长坡厚雪"，而非短期价格 | 长持仓页隐藏短期波动，突出基本面变化 |
| C9 | 量化派：回测与复盘模板 | 优矿 uqer.io | 系统化复盘——参数稳定性 / 滑点估计 / 过拟合检验；只看分布 | 增加"策略层"统计视图 |
| C10 | [老虎社区港美股复盘 SOP](https://www.laohu8.com) | 复盘君专栏 | 日内日志 = 行情快照 + 操作截图 + 60s 语音点评 | 支持截图与语音备注上传 |
| C11 | 刘建位：跟巴菲特学复盘 | 刘建位，央视《学习巴菲特》 | 年报式复盘——每年写一封"致自己的股东信" | 年度自动生成"个人股东信"摘要 |

### 1.2 英文社区（14 条）

| # | 标题 | 作者/来源 | 方法论核心 | TradingCoach 借鉴点 |
|---|------|----------|-----------|------------------|
| E1 | [Keeping a Trading Journal](http://traderfeed.blogspot.com/2019/05/trading-psychology-techniques-1-keeping.html) | Brett Steenbarger | 日记必须以一个 falsifiable goal 结束 | 每条复盘强制输出一个明日可验证目标 |
| E2 | [Best Practices Exercise](https://x.com/steenbab/status/1958665257498325245) | Brett Steenbarger | 列 top 5 mistakes，记录它们未发生时你做了什么 | 加"良好行为连击天数"维度 |
| E3 | [How to Conduct a Professional Review](https://www.smbtraining.com/blog/how-to-conduct-a-professional-review-of-your-trading) | Mike Bellafiore | 每笔交易 = performance test：prep / execution / stocks in play / 心态 | sizing/exit 作为独立评分轴，不混在 P&L 里 |
| E4 | [The Pro's Process](https://www.smbtraining.com/blog/the-pros-process-mike-bellafiore) | Bellafiore | replay tape → 看到的 vs 做的 → 明天的一个 drill | 复盘必须输出"明天要练的一个动作" |
| E5 | [Your best trading book is your own](https://www.adamhgrimes.com/your-best-trading-book-is-your-own-trading-book-four-steps-to-making-it-real/) | Adam Grimes | Dual journal：market research + behavior log 分离 | UI 拆分"setup 库"vs"行为日志" |
| E6 | [Trade Review of CREE](https://www.adamhgrimes.com/trade-review-cree/) | Adam Grimes | 单笔交易解剖：thesis / structure / 替代路径 / 哪里看对哪里看错 | 提供"引导式 post-mortem"模板 |
| E7 | [Decision Journal](https://fs.blog/wp-content/uploads/2017/02/decision-journal_draft3.pdf) | Shane Parrish, Farnam Street | 决策前记录情境 / 替代选项 / 预期 / 信心度（1-10）/ 身心状态 | 开仓时记 confidence + emotion，平仓时自动 resurface |
| E8 | [5 Things in Your Trading Journal](https://www.babypips.com/learn/forex/what-should-you-record-in-your-journal) | BabyPips | 市场背景 / setup / 入场出场止损 / R-multiple / 情绪 | 新用户的 MVP schema |
| E9 | [3 Prompts for Trading Psychology](https://www.babypips.com/trading/psychology-3-prompts-incorporate-psychology-trading-journal-2025-09-01) | BabyPips 2025 | 三个反思 prompt：身体状态 / 决策驱动 / 另一个自己 | 可选反思 prompt，随机弹出 |
| E10 | [Think & Trade Like a Champion ch. 4](https://www.amazon.com/Think-Trade-Like-Champion-Secrets/dp/0996307931) | Mark Minervini | 按 setup 分桶，算每桶 win rate / avg gain / avg loss / expectancy | 自动聚类交易，按 setup 出 expectancy |
| E11 | [Best Loser Wins – Book of Truths](https://www.amazon.com/Best-Loser-Wins-Thinking-high-stake/dp/085719822X) | Tom Hougaard | "残酷诚实的行为账本"——单独于交易日志，曝光自我欺骗 | "Uncomfortable Truths"私密字段，不出现在分享报告 |
| E12 | [System Self-Assessment](https://vantharpinstitute.com/course/psychology-of-trading-course/) | Van Tharp | 每个系统必须有：abort signal / 止盈出场 / 仓位规则 | 开平仓时强制"系统适配"checklist |
| E13 | [IBKR Significance of Journal](https://www.interactivebrokers.com/campus/trading-lessons/the-significance-of-maintaining-a-trading-journal/) | IBKR Campus | 字段：time / instrument / size / 理由 / 止损 / 目标 / 截图 / 情绪 / lesson | 提供"导出到券商格式"选项 |
| E14 | [Pabrai Checklist (Dhandho Investor)](https://www.oldschoolvalue.com/investment-tools/mohnish-pabrai-checklist-investor/) | Mohnish Pabrai | 97-item 清单来自"别人的错误"，决策前 15-20 分钟 | 社区错误清单可订阅 |

---

## 2. 复盘 KOL 名册（12 位）

### 2.1 中文 KOL (5 位)

- **邱国鹭** — 高毅资产 / 《投资中最简单的事》。贡献：三好+逆向框架。代表语录："便宜是硬道理。"（《投资中最简单的事》第二章）
- **段永平** — 雪球 @大道无形我有型。贡献：不为清单 + 本分。代表语录："做对的事情比把事情做对重要。"（雪球 2010 帖）
- **老唐（唐朝）** — 公众号"唐书房" / 《手把手教你读财报》。贡献：实盘日记+估值表周更范式。代表语录："别瞅傻子，瞅地。"
- **孟岩** — 有知有行 / 《孟岩》公众号。贡献：决策质量 vs 结果质量分离。代表语录："投资是认知的变现。"（有知有行第 50 期）
- **但斌** — 东方港湾 / 《时间的玫瑰》。贡献：长期持有 + 季度重置测试。

### 2.2 英文 KOL (7 位)

- **Brett Steenbarger** — TraderFeed blog / *The Daily Trading Coach*。贡献：journal as behavioral lab。代表语录："The goal of journaling is not to record trades but to change them."
- **Mike Bellafiore** — *One Good Trade* / *The Playbook*。贡献：勾画 prop desk 的 Playbook 范式。代表语录："Every trade is a performance test, not a lottery ticket."
- **Adam Grimes** — *The Art and Science of Technical Analysis*。贡献：双日记法 (market + behavior)。代表语录："Keeping a trading journal is one of the practices that consistently separates winning from losing traders."
- **Tom Hougaard** — *Best Loser Wins*。贡献：Book of Truths。代表语录："Most traders don't lose because they lack knowledge — they lose because they can't execute what they already know."
- **Mark Minervini** — *Think & Trade Like a Champion*。贡献：分桶量化 post-analysis。代表语录："Diligent trade journal maintenance is the detail that separates winners from losers."
- **Van K. Tharp** — *Trade Your Way to Financial Freedom*。贡献：R-multiples + 系统自评。代表语录："You don't trade the markets; you trade your beliefs about the markets."
- **Linda Raschke** — *Trading Sardines*。代表语录："Writing down your trades is the best exercise in the world."

---

## 3. 大师对复盘的思考（39 位）

### 3.1 中文 13 位

| 大师 | 引语 | 出处 | TradingCoach 启发 |
|------|-----|-----|------------------|
| 邱国鹭 | "便宜是硬道理" | 《投资中最简单的事》 | 评分加"买入估值分位"维度 |
| 段永平 | "投资就是不做不懂的事" | 雪球 2011 帖 | 不熟标的标"超出能力圈" |
| 林园 | "只赚自己看得懂的钱" | 《林园投资 36 计》 | 赛道白名单功能 |
| 但斌 | "时间是优秀企业的朋友" | 《时间的玫瑰》序 | 持仓时长加分项 |
| 张磊 | "守正用奇，弱水三千，但取一瓢" | 《价值》自序 | 集中度可视化 |
| 刘建位 | "巴菲特从不平均，他重仓深度研究的" | 《巴菲特选股 10 招》 | 突出 Top 5 持仓贡献 |
| 唐朝 | "看不懂就不要碰，不懂不做" | 《价值投资实战手册》 | 强制"我懂这家公司"勾选 |
| 孟岩 | "好的决策可能短期亏钱，差的决策可能短期赚钱" | 有知有行播客 | 过程/结果双指标 |
| 巴菲特 (中) | "规则一：不要亏损；规则二：记住规则一" | 中信《巴菲特致股东的信》 | 最大回撤红线提醒 |
| 芒格 | "反过来想，总是反过来想" | 《穷查理宝典》 | 复盘加"反向操作会怎样"反事实模块 |
| 彼得林奇 | "投资股票前，先用 2 分钟说清楚理由" | 中信《彼得林奇的成功投资》 | 限 140 字买入理由 |
| 霍华德马克斯 | "你不能预测，但可以准备" | 中信《投资最重要的事》 | 应对剧本而非预测页面 |
| 达里欧 (中) | "痛苦+反思=进步" | 中信《原则》 | 亏损交易强制写反思 |

### 3.2 英文 26 位

| Master | Quote (Source) | TradingCoach Inspiration |
|--------|---------------|--------------------------|
| Buffett | "It is not necessary to do extraordinary things to get extraordinary results." (1994 Berkshire letter) | 奖励一致性，弱化英雄交易 |
| Munger | "I'll perform better if I rub my nose in my mistakes." (DJCO 2018) | 错误置顶展示 |
| Soros | "I'm only rich because I know when I'm wrong." (*Soros on Soros*, Wiley 1995) | 评分"识别错误的时间" |
| Druckenmiller | "When the circumstances change, you have to change." (Hustle Q&A 2015) | 跟踪 thesis-change 事件 |
| Dalio | "Pain + reflection = progress." (*Principles*, S&S 2017) | 亏损后强制反思步骤 |
| Livermore | "...in losing money I have gained valuable don'ts." (*Reminiscences*, 1923) | 建"don'ts"库 |
| Kovner | "Undertrade, undertrade, undertrade." (*Market Wizards*, 1989) | 标记 oversize 仓位 |
| Paul Tudor Jones | "Losers average losers." (*Market Wizards*, 1989) | 自动检测加仓亏损 |
| Steinhardt | "Variant perception." (*No Bull*, Wiley 2001) | 开仓问"共识怎么看" |
| Robertson | "Avoid big losses." (*Julian Robertson*, Strachman 2004) | 风控权重高于收益最大化 |
| Kahneman | "Imagine we are a year in the future…" (*Thinking, Fast and Slow*, 2011) | 预 mortem 字段 |
| Annie Duke | "A great decision is the result of a good process… not a great outcome." (*Thinking in Bets*, 2018) | 过程分与 P&L 分解耦 |
| Howard Marks | "You can't predict. You can prepare." (Oaktree memo 2001-11-20) | 准备质量独立打分 |
| Klarman | "Margin of safety… room to be wrong." (GS Talks) | "headroom-to-stop"指标 |
| Peter Lynch | "Know what you own, and know why you own it." (*One Up On Wall Street*, 1989) | 必填两句 thesis |
| Templeton | "The four most dangerous words: 'this time it's different.'" | 检测 thesis 是否含该模式 |
| Schloss | "We try to buy stocks cheap…" (Schloss letter 1989) | 入场纪律检查 |
| Pabrai | "The basis for my checklist is the mistakes of great investors." (*Dhandho*, 2007) | 社区错误清单 |
| Guy Spier | "Checklists reduce errors from cognitive bias." (*Education of a Value Investor*, 2014) | 开仓前 checklist UI |
| Minervini | "What separates the great from the good is post-analysis." (paraphrased) | post-analysis 为一等公民 |
| Raschke | "Writing down your trades is the best exercise in the world." | 降低写作摩擦 |
| Seykota | "Everybody gets what they want out of the market." (*Market Wizards*, 1989) | 检测自我破坏模式 |
| Schwartz | "Separate my ego from making money…" (*Pit Bull*, 1998) | 标记 ego-driven 交易 |
| Grimes | "Your best trading book is your own." | 用户拥有 playbook 导出权 |
| Steenbarger | "Best practices reveal themselves when we're not f*cking up." (X, 2025) | 高亮干净日，不只盯坏日 |
| Bellafiore | "One Good Trade." (book title 2010) | "Trade of the day"高亮 feature |

---

## 4. 跨文化共性主题（CN/EN 对照）

| 主题 | 中文圈表达 | 英文圈表达 | 共识强度 |
|------|----------|----------|---------|
| **过程优于结果** | 孟岩"决策质量 vs 结果质量"、段永平"做对的事情" | Annie Duke、Steenbarger、Marks | ⭐⭐⭐⭐⭐ |
| **能力圈即不为清单** | 段永平"不为清单"、唐朝"不懂不做"、林园"赛道清单" | edge/conviction，但更弱 | 中文圈更强 |
| **赛道思维** | 林园/但斌/张磊先框赛道再选股 | Minervini 按 setup 分桶 | CN 偏行业 / EN 偏 setup |
| **持续 > 完美** | 唐朝"周更十年"、孟岩仪式感 | Grimes/Raschke 低摩擦 | ⭐⭐⭐⭐ |
| **情绪与人性** | 知乎/雪球大量情绪日记 | Steenbarger/Hougaard 但更系统化 | CN 散文 / EN 结构 |
| **致股东信式年度复盘** | 刘建位/唐朝/孟岩仪式感 | 英文圈罕见 | 中文圈独有 |
| **预 mortem & 决策日志** | 中文圈较少明确 | Kahneman/Parrish/Pabrai 强 | EN 圈更强 |
| **错误 > 成功的学习价值** | 段永平/芒格"反过来想" | Munger/Livermore/Pabrai "don'ts" | ⭐⭐⭐⭐⭐ |

**关键差异**：中文圈侧重"价值投资的内省与仪式感"，英文圈侧重"行为科学的结构化拆解"。TradingCoach 作为双语产品，应吸收 **CN 仪式感 + EN 结构化** 的并集。

---

## 5. 同类产品 Landscape（14 款）

### 5.1 Feature Matrix

| 产品 | CSV 自动 | 多券商 | 标签 | 截图 | Replay | 策略分类 | 目标 | 行为分析 | 移动端 | API | 免费版 |
|------|--------|-------|------|------|--------|---------|------|--------|-----|-------|
| Tradervue | ✓ | ✓ | ✓ | ✓ | partial | ✓ | partial | partial | ✗ | ✓ | ✓ |
| Edgewonk | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ | partial | ✗ |
| TraderSync | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (AI) | ✓ | partial | trial |
| Chartlog | ✓ | ✓ | ✓ | ✓ | partial | ✓ | partial | ✗ | ✗ | ✗ | trial |
| TradeBench | partial | ✓ | ✓ | ✓ | ✗ | partial | ✓ | ✗ | ✗ | ✓ | ✓ |
| TradingDiary Pro | ✓ | ✓ | ✓ | partial | ✗ | ✓ | partial | ✗ | ✗ | ✓ | ✗ |
| Trademetria | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | partial | ✗ | ✓ (REST) | ✓ |
| Trademan | partial | partial (IBKR) | ✓ | ✓ | partial | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Tradezella | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | partial | ✗ | partial | ✗ |
| TraderMake.Money | ✓ (exch) | ✓ (crypto) | ✓ | ✓ | ✗ | ✓ | ✓ | partial | ✓ | ✓ | ✓ |
| Notion/Obsidian | ✗ | ✗ | ✓ | ✓ | ✗ | partial | ✓ | ✗ | ✓ | ✓ | ✓ |
| 同花顺投资账本 | partial | partial (A 股) | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | ✓ |
| 复盘盒子 | ✗ | ✗ | ✓ | ✓ | partial | partial | ✗ | ✗ | ✓ | ✗ | ✓ |
| 海豚财富 | ✗ | ✗ (华林) | partial | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | ✓ |

### 5.2 White-Space（TradingCoach 的差异化窗口）

1. **Counterfactual "What-If"** — Edgewonk 只有 alt-strategy；其他无人做"如果你持有 30 分钟，P&L = X"基于真实数据的 counterfactual。TradingCoach 已有 cf1-cf5 引擎，独占。
2. **双语 + Futu/IBKR HK 原生** — 零产品支持 Futu CN+EN CSV / HKD+USD 双币种 / HKT+ET 时区 / 期权符号（`NVDA260618C205`）。无竞争 wedge。
3. **HK + US 混合账户分析** — 西方工具假设 USD-only，中文工具假设 A 股-only。港美股+港股+期权混合账户结构性空白。
4. **行为锚定 AI 教练** — TraderSync 的 Cypher / Edgewonk 的 Edge Finder 给的都是"周二表现好"这种泛泛之言。基于用户 8 维评分 + counterfactual delta 才能输出"你在 7/10 NVDA 财报交易里提前 12 分钟离场，损失 $4,300"。
5. **期权 spread + 隐私截图分享** — 只有 TradingDiary Pro/Trademetria 处理 multi-leg P&L 且 UI 难看。"打码账户大小+股票代码"的隐私分享模式是 viral 钩子。

---

## 6. Feature 路线图（15 个，按 ROI/Effort 排序）

### Tier 1 — 低 Effort × 高 ROI（4 个，Q3 2026）

#### F1. 决策日志 (Decision Journal)
- **依据**: C3, C4, E7, E14 (Pabrai)、彼得林奇 / Parrish / 唐朝
- **what**: 开仓时强制 2 字段——`thesis_140char`（≤140 中文/英文字）、`exit_trigger`（什么情况会让我卖）。平仓时自动 resurface，提示用户做 retrospective。
- **API**: `POST /api/v1/positions/{id}/decision-log` `{thesis, exit_trigger, confidence_1_10, emotion_tag}`
- **UI**: 开仓后弹一次性 dialog（5 个字段），平仓后在交易详情页置顶展示。
- **Effort**: 后端 0.5d，前端 1d。
- **ROI**: 解锁后续所有"过程分"feature 的数据基础。

#### F2. 过程分/结果分双轴展示
- **依据**: C4 (孟岩)、E5/E6 (Grimes)、Annie Duke、Howard Marks
- **what**: V2 评分已经包含技术/行为/风控等 8 维，但目前只有总分。拆分为 `process_score` (技术+行为+风控+决策) 和 `outcome_score` (盈亏分位)，在交易卡片同屏展示。
- **API**: 现有 `scoring.compute_v2()` 返回结构已经有这些维度，只需 expose 两个 aggregate 字段。
- **UI**: 散点图 X=过程分, Y=结果分；四象限：好决策好结果 / 好决策坏结果（运气差，可接受）/ 坏决策好结果（运气好，要警惕）/ 坏决策坏结果。
- **Effort**: 后端 0.5d，前端 1.5d。
- **ROI**: 直接命中跨文化 #1 共性主题。

#### F3. 错误分类二分（违纪 vs 概率）
- **依据**: C2 段永平、Livermore "don'ts"、Pabrai 错误清单、Munger
- **what**: 用户在亏损交易（PnL < 0）的复盘里勾选"违纪类型"——`broke_stop_loss` / `oversized` / `revenge_trade` / `out_of_circle` / `not_violation_just_unlucky`。系统聚合后给出"违纪类亏损 $X / 概率类亏损 $Y"。
- **API**: `POST /api/v1/positions/{id}/error-tag` `{tags: [...]}` (multi-select)
- **UI**: 亏损交易页面右上角"标记错误类型"，月度/年度报告里出"违纪 vs 概率"饼图。
- **Effort**: 后端 0.5d，前端 1d。
- **ROI**: 让 counterfactual 引擎的 cf1-cf5 有了"哪些规则该 enforce"的用户反馈。

#### F4. 周度复盘模板 (Weekly Retro Loop)
- **依据**: E1/E2 (Steenbarger)、E3/E4 (Bellafiore)、唐朝
- **what**: 每周日推送一份模板——本周 3 个最佳交易 + 3 个最差交易，模板要求用户为下周写一个 "明天/下周要练的一个动作" (强制单数)。系统跟踪连续完成情况。
- **API**: `POST /api/v1/retro/weekly` `{week_start, best_3, worst_3, next_drill}`
- **UI**: 单页向导，3 步完成。dashboard 显示"已连续复盘 X 周"。
- **Effort**: 后端 1d，前端 2d。
- **ROI**: 形成习惯，提高 retention。

### Tier 2 — 中 Effort × 高 ROI（5 个，Q4 2026）

#### F5. 年度致股东信自动生成
- **依据**: C11 (刘建位)、唐朝、孟岩、Buffett 1994 致股东信
- **what**: 年终一键生成"致自己的股东信"PDF——包含总收益、跑赢/跑输基准、Top 5 持仓贡献、3 大错误反思、明年承诺。所有数据来自系统，文字由 GPT 模板化润色。
- **API**: `POST /api/v1/reports/annual-letter` `{year}` → PDF
- **UI**: 12 月底自动入口，让用户编辑 4 个字段后生成。
- **Effort**: 后端 2d（含 PDF 渲染），前端 1d。
- **ROI**: 中文圈独有仪式感，强 viral（用户会主动分享朋友圈）。

#### F6. 引导式 Post-Mortem 模板
- **依据**: E6 (Grimes CREE)、E3 (Bellafiore)、E10 (Minervini)
- **what**: 每笔交易提供 5 个引导问题：`thesis_was`, `what_was_right`, `what_was_wrong`, `if_redo`, `next_drill`. 用户答完，系统自动 tag 关键词聚合。
- **Effort**: 后端 1d，前端 1.5d。
- **ROI**: 让低活跃用户也能写出有质量的复盘。

#### F7. 情绪标签 + 与亏损相关性
- **依据**: C5 (知乎)、E9 (BabyPips 2025)、Hougaard
- **what**: 开仓时选 emotion（FOMO/平静/恐惧/贪婪/复仇），平仓后系统给"按情绪分组的胜率/盈亏"。
- **Effort**: 后端 1d，前端 2d。
- **ROI**: 让用户看到自己的情绪定价。

#### F8. 行为锚定 AI 教练
- **依据**: TraderSync Cypher 痛点、E2 (Steenbarger best practices)、White-space #4
- **what**: 基于用户 8 维评分 + counterfactual delta + 情绪标签，每周生成 3 条 actionable insight。例："你在 NVDA 财报前 7 笔交易里有 5 次提前 12 分钟离场，导致 $4,300 损失。建议下次设 trailing stop 而非 hard exit。"
- **API**: `GET /api/v1/coach/weekly-insights`
- **UI**: 主页顶部 3 张卡片，每条带"应用此建议"按钮（链到具体 setting）。
- **Effort**: 后端 3d（含 prompt 工程），前端 1d。
- **ROI**: 最具产品差异化，决定用户长期留存。

#### F9. Setup 分桶 + 每桶 Expectancy
- **依据**: E10 (Minervini)、E12 (Van Tharp R-multiples)、Bellafiore Playbook
- **what**: 用户给交易打 setup tag（突破/回踩/反转/财报/事件/...），系统按 setup 算 win rate / avg gain / avg loss / expectancy，按 expectancy 降序排。
- **API**: `GET /api/v1/stats/by-setup`
- **UI**: 表格 + 漏斗图，最差 setup 标红"建议剔除"。
- **Effort**: 后端 1.5d，前端 1.5d。
- **ROI**: 让用户看到"哪类交易应该放弃"。

### Tier 3 — 高 Effort × 高 ROI（3 个，Q1 2027）

#### F10. 隐私模式截图分享
- **依据**: White-space #5、Hougaard Book of Truths（私密）
- **what**: 一键生成"打码"截图——账户金额→百分比、股票代码→`XXXX`、用户名→匿名。用户可选公开分享或仅好友。
- **Effort**: 后端 2d（图片合成），前端 2d。
- **ROI**: viral 钩子，每次分享=广告。

#### F11. 赛道白名单 (Watchlist Bands)
- **依据**: C6 (林园)、C8 (张磊)、唐朝、段永平能力圈
- **what**: 用户自定义"我懂的赛道"（消费/医药/AI/...），赛道外的交易在 UI 标红，月度报告专门统计"赛道外亏损"。
- **Effort**: 后端 2d，前端 2d。
- **ROI**: 强化能力圈纪律。

#### F12. 反事实回测 v2 — 用户可自定义规则
- **依据**: 现有 cf1-cf5 引擎、Edgewonk alt-strategy、White-space #1
- **what**: 用户可拖拽组合规则（"如果第一个月亏损 > -5% 就停止交易 X 天" + "如果连续 3 笔亏损就 size 减半"），系统算如果应用这些规则，过去一年 P&L 会变成多少。
- **Effort**: 后端 3d（规则 DSL 设计），前端 3d（rule builder UI）。
- **ROI**: 独占壁垒，最强差异化。

### Tier 4 — 低优先（3 个，可观察）

#### F13. 决策清单订阅（社区版）
- **依据**: E14 (Pabrai 97-item)、Spier
- **what**: 公开错误清单订阅（"巴菲特错误集"/"段永平不为清单"/"用户A 公开清单"），开仓前必跑一次。

#### F14. 语音备注 + 60s 点评
- **依据**: C10 (老虎社区)
- **what**: 移动端可录 60s 语音备注挂在交易记录上，未来 AI 转文字 + 情绪检测。

#### F15. 良好行为连击天数
- **依据**: E2 (Steenbarger best practices)
- **what**: 系统检测"无违纪交易日"连击，类似 Duolingo streak，奖励持续纪律。

---

## 7. 推荐执行顺序（6 个月排期）

```
Month 1-2 (Q3 2026):  F1 + F2 + F3   → 数据底座 + 过程/结果双轴
Month 3   (Q3 2026):  F4              → 周度复盘形成习惯
Month 4   (Q4 2026):  F5 + F7         → 年度仪式 + 情绪分析（中文圈强）
Month 5   (Q4 2026):  F6 + F9         → Post-mortem + Setup 分桶（英文圈强）
Month 6   (Q1 2027):  F8 + F10        → AI 教练 + 隐私分享（差异化 + viral）
观察期:               F11/F12/F13-15  → 根据 retention 决定
```

---

## 8. 关键参考文献完整列表（25 条 URL）

中文：
1. https://xueqiu.com/1494750910 (邱国鹭)
2. https://xueqiu.com/6246718469 (段永平)
3. https://youzhiyouxing.cn (孟岩)
4. https://www.zhihu.com/question/27983890 (路过銀河)
5. https://www.laohu8.com (老虎社区)
6-11. 唐书房、林园专栏、《时间的玫瑰》、《价值》、优矿、刘建位（央视）— 多为微信公众号/书籍引用

英文：
12. http://traderfeed.blogspot.com/2019/05/trading-psychology-techniques-1-keeping.html
13. https://x.com/steenbab/status/1958665257498325245
14. https://www.smbtraining.com/blog/how-to-conduct-a-professional-review-of-your-trading
15. https://www.smbtraining.com/blog/the-pros-process-mike-bellafiore
16. https://www.adamhgrimes.com/your-best-trading-book-is-your-own-trading-book-four-steps-to-making-it-real/
17. https://www.adamhgrimes.com/trade-review-cree/
18. https://fs.blog/wp-content/uploads/2017/02/decision-journal_draft3.pdf
19. https://www.babypips.com/learn/forex/what-should-you-record-in-your-journal
20. https://www.babypips.com/trading/psychology-3-prompts-incorporate-psychology-trading-journal-2025-09-01
21. https://www.amazon.com/Think-Trade-Like-Champion-Secrets/dp/0996307931
22. https://www.amazon.com/Best-Loser-Wins-Thinking-high-stake/dp/085719822X
23. https://vantharpinstitute.com/course/psychology-of-trading-course/
24. https://www.interactivebrokers.com/campus/trading-lessons/the-significance-of-maintaining-a-trading-journal/
25. https://www.oldschoolvalue.com/investment-tools/mohnish-pabrai-checklist-investor/

竞品 Landscape：
- https://www.tradervue.com/
- https://edgewonk.com/
- https://tradersync.com/
- https://www.chartlog.com/
- https://tradebench.com/
- https://www.tradingdiarypro.com/
- https://trademetria.com/pricing
- https://trademan.app/
- https://www.tradezella.com/pricing
- https://tradermake.money/prices
- https://www.notion.com/templates/category/trading-journal
- https://www.10jqka.com.cn/ (同花顺)
- https://sj.qq.com/appdetail/com.fupanhezi.app (复盘盒子)
- https://sj.qq.com/appdetail/com.weizq (海豚财富)

---

**报告字数**: ~5500 字 | **覆盖深度**: 文章 25 / KOL 12 / 大师 39 / 产品 14 | **可立即落地的 Feature**: 15 个（Tier 1 共 4 个 < 一周可启动）
