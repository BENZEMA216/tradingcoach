# TradingCoach 交易复盘全景研究与 Feature 路线图

> 一旦本文件所属内容有变化，请同步更新 `project_docs/readme.md` 索引。
>
> **生成时间**: 2026-05-20
> **研究范围**: 25 篇方法论文章、12 位复盘 KOL、39 位投资大师语录、14 款同类产品 landscape
> **目的**: 为 TradingCoach 后续 6 个月的复盘能力建设提供研究底座 + 可落地 Feature 列表

---

## 0. 执行摘要 (TL;DR) — v2 (2026-05-20 reframe)

### 产品定位公理

**TradingCoach 不是 trading journal，是 trading post-mortem analyst。**

> **Slogan**: 「你不用记，我们帮你看见。」

用户唯一输入是 CSV。系统输出是「看见」——看见你看不见的行为模式、看见错误的真实价格、看见你与典型风格的差距。用户从「被要求填写」变成「被告知发现」。

### 为什么是这个定位

1. **认知科学硬约束**：散户事后 100% 记不得当初为什么买。要求用户高纪律记录的 journal 范式（Tradervue / Edgewonk / Steenbarger / 老唐手把手日记）在散户身上结构性失效。
2. **跟竞品差异化**：所有同类产品都是"笔记本"，没人是"事后分析师"。这是真正的蓝海空白，比"中英双语+港美股"差异化更上一层。
3. **跟 LLM 时代契合**：2026 年的 LLM 已经能从交易数据反推 thesis、识别行为模式、生成分析报告——这些以前必须用户填，现在系统能猜出 80%。

### 设计 Gate（任何新 feature 必过）

**问：如果用户什么都不填，这个功能还有价值吗？** 必须是 yes，否则废弃。

### Top 5 v2 Feature（详见 §6）

1. **G0 行为模式自动检测库** — 产品基石。从 CSV 自动识别 20+ 种用户看不见的行为模式（复仇交易/追涨/砍底部/提前离场/连亏加仓/...）
2. **G3 AI 周/月/季/年复盘报告** — 主要触点。系统自动生成"分析师写给散户"的文字报告，零用户输入
3. **G7 复盘问答 Chatbot** — 杀手 feature。用户自然语言提问，LLM 用全部交易数据 + G0 事件流 + counterfactual 作为上下文回答
4. **G4 错误价签** — Viral 钩子。"你这个习惯一年花了你 $4,300"，让错误有价格标签
5. **F12 反事实回测 v2** — 独占壁垒。基于真实交易数据的 counterfactual，主要竞品都做不到

### 保留 vs 砍掉

- ✅ **保留**：F2 (过程/结果双轴), F5 (年度股东信), F8 (AI 教练→改造为 G3 一部分), F10 (隐私分享), F11 (赛道白名单), F12 (反事实回测), F15 (行为连击)
- ❌ **砍掉/改造**：F1 (决策日志→G1 AI 反推 thesis), F3 (错误打 tag→G0 自动检测), F4 (周报模板→G3 AI 生成), F6 (引导 post-mortem→G3 一部分), F7 (情绪 tag→G0 行为推断), F9 (setup tag→G6 AI 识别), F13 (清单订阅), F14 (语音备注)

**结果：用户填写动作从 8 个降到 0 个。全程只需「上传 CSV → 看报告 → 提问」。**

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

## 6. Feature 路线图 v2 — 「事后整体复盘」视角（2026-05-20 reframe）

> **重要**：v1 路线图（F1-F15）的 8 个功能要求用户主动填写（决策日志、错误打 tag、周报、情绪 tag、setup tag 等），违反"用户事后记不得"公理，已废弃。v2 重组为「零负担复盘」路线，所有 G 系列功能在用户什么都不填的前提下仍有完整价值。

### 6.0 v1 → v2 映射表

| v1 Feature | v2 处理 | 原因 |
|------------|---------|------|
| F1 决策日志（用户开仓填） | → **G1** AI 反推 thesis 考古 | 用户记不得，改 AI 反推 |
| F2 过程/结果双轴 | ✅ 保留为 **G2** | 现有数据即可，无需用户填 |
| F3 错误分类（用户打 tag） | → **G0** 自动检测违纪 | 用户事后打也会失真 |
| F4 周度复盘模板（用户写） | → **G3** AI 自动生成周报 | 用户不会写 |
| F5 年度致股东信 | ✅ 保留为 **G3** 一部分 | 已经是 AI 生成 |
| F6 引导 post-mortem（用户填） | → **G3** AI 草稿 | 改为系统先写，用户只改 |
| F7 情绪 tag（用户开仓选） | → **G0** 从行为推断 | 追高=贪婪/砍底部=恐惧 |
| F8 行为锚定 AI 教练 | → **G3** 主要输出 | 升级为完整报告 |
| F9 Setup 分桶（用户打 tag） | → **G6** AI 识别 setup | 突破/回踩/财报 LLM 能识别 |
| F10 隐私截图分享 | ✅ 保留 | 无需用户填 |
| F11 赛道白名单 | ✅ 保留（一次性配置） | 配置后系统自动判 |
| F12 反事实回测 v2 | ✅ 保留 | 独占壁垒 |
| F13 决策清单订阅 | ❌ 砍 | 违反公理 |
| F14 语音备注 | ❌ 砍 | 违反公理 |
| F15 行为连击天数 | ✅ 保留 | 系统自动统计 |

### Tier 1 — 产品基石（Month 1-2, Q3 2026）

#### 🌟 G0. 行为模式自动检测库（**最重要**）
- **依据**: TradingCoach 8 维评分 + counterfactual delta + 跨文化共性主题（错误 > 成功的学习价值）
- **what**: 从 CSV 自动识别用户看不见的行为模式。每种模式 = 一个可被 query 的事件流。MVP 20 种：
  - **冲动类**：复仇交易（亏损后 1h 内开新仓）、追涨（突破后 5% 进）、FOMO（连续 N 天上涨后追入）
  - **执行类**：砍在底部（亏损超 X% 才止损）、提前离场（出场后该股继续涨 > Y%）、止损不严（实际止损位远于预设）
  - **加仓类**：连亏后加仓（M2M 思维）、单股过度集中、跨账户相互掩盖
  - **时间类**：周一效应、周五效应、季度尾效应、过度交易日（>N 笔/日）
  - **品种类**：期权 IV 高位买入、低流动性标的、首次接触新行业
  - **赛道类**：能力圈外交易（结合 F11/G8 赛道白名单）
- **API**: `GET /api/v1/behavior/patterns?from=&to=` → `[{pattern_id, position_ids, severity, pnl_impact, ...}]`
- **数据模型**: 新表 `behavior_events`，每次 import/recompute 时刷新
- **UI**: 这是引擎层，本身不展示。但 G3/G4/G7 全部消费这个事件流
- **Effort**: 后端 5d（20 种规则 + 测试），前端 0d
- **ROI**: 后续所有零负担 feature 的数据底座

#### 🌟 G2. 过程分 / 结果分双轴展示（原 F2）
- **依据**: C4 (孟岩)、Annie Duke、Howard Marks
- **what**: V2 评分已经包含 8 维，拆分为 `process_score`（技术+行为+风控+决策）和 `outcome_score`（盈亏分位），同屏散点图
- **API**: `scoring.compute_v2()` 返回值已含数据，新增 aggregate endpoint
- **UI**: 四象限散点图：好决策好结果 / 好决策坏结果（运气差）/ 坏决策好结果（要警惕）/ 坏决策坏结果
- **Effort**: 后端 0.5d，前端 1.5d
- **ROI**: 跨文化共识 #1，让用户第一次区分"决策"和"运气"

### Tier 2 — 主要表现层（Month 3-4, Q3-Q4 2026）

#### 🌟 G3. AI 周/月/季/年复盘报告（**主要触点**）
- **依据**: E1/E2 (Steenbarger)、E3/E4 (Bellafiore "next drill")、C11 (刘建位致股东信)、唐朝、孟岩、TraderSync Cypher 痛点
- **what**: 系统每周一/月初/季初/年初**自动**生成"分析师写给散户"的文字报告。零用户输入。报告结构（4 段）：
  1. **本期画像**：N 笔交易，胜率 X%，平均持仓 Y，最大单笔 +Z%/-W%
  2. **Top 3 错误**（消费 G0 事件流）+ 错误价签：复仇交易 3 次 → 损失 $1,200
  3. **Top 3 亮点**：连续 5 天遵守止损、NVDA 仓位控制得当
  4. **与上期对比**：止损纪律改善 +15% / 仓位过大恶化 -8%
  5. **下期 1 个建议**（强制单数，仿 Bellafiore "next drill"）：每条带"应用此建议"按钮，直链具体 setting
- **API**: `GET /api/v1/reports/auto?period=weekly|monthly|quarterly|annual`
- **UI**: 首页顶部卡片"本周复盘报告已生成"。点击进入全屏阅读。年度报告生成 PDF 可分享
- **LLM 调用**: 把 G0 事件流 + V2 评分 + counterfactual 喂给 LLM，prompt 模板按周期切换语气（周报偏战术、年报偏 Buffett 致股东信仪式感）
- **Effort**: 后端 4d（含 prompt 工程 + PDF 渲染），前端 2d
- **ROI**: 用户日常的唯一触点。所有研究投入 → 通过这一张报告兑现给用户

#### 🌟 G4. 错误价签（**Viral 钩子**）
- **依据**: White-space #4 行为锚定教练、Steenbarger 行为成本量化
- **what**: G0 检测到的每种错误模式自动计算"这个习惯一年花了你多少钱"：
  - "连亏后加仓" 一年损失 $4,300
  - "提前离场" 一年错过 $2,100
  - "复仇交易" 一年损失 $890
  - **总坏习惯成本**：年化 $7,290（占总盈亏 18%）
- **计算**: 行为模式触发的交易 P&L 减去 counterfactual P&L（即"如果没犯这个错"的应得收益）
- **API**: `GET /api/v1/behavior/cost-tags?period=annual`
- **UI**: 单独 dashboard 页"我的坏习惯账单"。每个 tag 一张大数字卡片。一键分享为打码图（联动 F10）
- **Effort**: 后端 1.5d，前端 2d
- **ROI**: 最强 viral 钩子。用户主动分享朋友圈"我今年因为复仇交易亏了 $4,300"

### Tier 3 — 杀手 Feature & 差异化（Month 5-6, Q4 2026 / Q1 2027）

#### 🌟 G7. 复盘问答 Chatbot（**杀手 feature**）
- **依据**: 事后整体复盘的最自然交互形态、LLM 时代必然路径
- **what**: 用户自然语言提问，LLM 用全部交易数据 + G0 行为事件流 + counterfactual 结果作为上下文回答：
  - "我今年 NVDA 表现怎样？"
  - "我什么时候最容易亏钱？" → "周五下午 14:00 后，胜率从 52% 降到 31%"
  - "我的止损策略有用吗？" → 自动跑 counterfactual 对比
  - "如果我严格执行所有止损，会多赚多少？"
  - "我有没有过度交易？" → 检测 G0 时间类模式
  - "TSLA 和 NVDA 我哪个做得更好？"
- **架构**: 把用户的交易数据 + G0 事件流 + V2 评分 + counterfactual 序列化成结构化 context（≤200K tokens），喂给 Claude/GPT。配合 function calling 允许 LLM 触发系统计算
- **API**: `POST /api/v1/chat` `{message, session_id}` → streamed response
- **UI**: 浮动 chat 按钮 + 完整 chat 页。支持引用具体交易/图表
- **Effort**: 后端 7d（context 序列化 + function calling），前端 4d
- **ROI**: 杀手级。这才是真正的"事后分析师"，决定用户长期留存

#### G6. AI 自动 Setup 识别（原 F9 改造）
- **依据**: E10 (Minervini 按 setup 分桶)、E12 (Van Tharp)、White-space #4
- **what**: LLM + 技术指标自动识别每笔交易的 setup 类型（突破/回踩/反转/财报前/事件驱动/IV crush/...）。不让用户打 tag
- **API**: `POST /api/v1/positions/{id}/setup-detect` (batch)
- **UI**: 自动按 setup 分桶展示 win rate / expectancy。最差 setup 标红 "G3 报告里会提醒你戒掉此 setup"
- **Effort**: 后端 3d（特征工程 + LLM prompt），前端 1d
- **ROI**: 让 G0/G3 报告里的"行为模式"更细粒度

#### G8. 风格定位 + 双胞胎对照
- **依据**: 跨文化共识、白皮书 "我是谁" 范式
- **what**: 把用户与 N 种典型风格对比（短线狙击 / 趋势跟随 / 价值长持 / 事件驱动 / 期权策略 / 韭菜散户）：
  - 风格画像："你其实是趋势跟随者，但你在做短线狙击——这是你亏钱的根本原因。"
  - 双胞胎：找出用户做过的相似交易（同 setup / 同股票 / 同行业）：
    - "你在 NVDA 财报前 8 次交易胜率 25%，平均亏 $X — 这个 setup 对你无效"
    - "你 80% 的科技股盈利来自周二、80% 的亏损来自周五"
- **API**: `GET /api/v1/profile/style` / `GET /api/v1/positions/{id}/twins`
- **UI**: 个人画像页 + 每笔交易底部"相似历史交易"
- **Effort**: 后端 4d（聚类 + LLM 标注），前端 3d
- **ROI**: 强情绪冲击。让用户第一次"看见自己"

#### F10. 隐私模式截图分享（保留）
- **what**: 一键打码截图，金额→%、股票代码→`XXXX`、用户名→匿名
- **Effort**: 后端 2d，前端 2d
- **ROI**: viral 钩子。配合 G4 错误价签效果最大化

#### F11. 赛道白名单（保留，一次性配置）
- **what**: 用户一次性配置"我懂的赛道"，赛道外交易自动标红 + 进 G0 "能力圈外"事件流
- **Effort**: 后端 2d，前端 2d
- **ROI**: 强化能力圈纪律。中文圈共识

#### F12. 反事实回测 v2（保留，最强差异化）
- **what**: 用户拖拽组合规则，系统跑 counterfactual。例："如果连续 3 笔亏损就 size 减半 + 单股 < 20% 仓位"，过去一年 P&L 会变成多少
- **Effort**: 后端 3d（DSL），前端 3d（rule builder）
- **ROI**: 独占壁垒，竞品做不到

### Tier 4 — 可观察（2 个）

#### F15. 良好行为连击天数
- **what**: 系统检测"无违纪交易日"连击（依赖 G0），类似 Duolingo streak
- **ROI**: retention 工具

#### G9. 社区错误模式订阅（替代 F13）
- **what**: 用户可订阅"段永平不为清单 → 自动映射为 G0 检测规则"、"巴菲特规避错误 → 自动检测"。不是订阅清单让用户对照，是订阅规则让系统帮你查
- **ROI**: 差异化护城河，等社区起来再做

---

## 7. 推荐执行顺序 v2（6 个月排期）

```
Month 1-2 (Q3 2026):  G0 (行为模式检测 20 种)     [产品基石 — 后续全部依赖]
                      G2 (过程/结果双轴)          [现有数据即可]
Month 3   (Q3 2026):  G3 (AI 周/月报告 v1)        [主要触点]
                      G4 (错误价签)              [Viral 钩子]
Month 4   (Q4 2026):  G6 (AI Setup 识别)          [G3 细粒度增强]
                      G3 (季报/年报扩展)
Month 5   (Q4 2026):  G7 (复盘问答 Chatbot)       [杀手 feature]
                      G8 (风格定位 + 双胞胎)
Month 6   (Q1 2027):  F10 (隐私分享)              [Viral 闭环]
                      F12 (反事实回测 v2)         [差异化护城河]
观察期:               F11 (赛道白名单)
                      F15 (行为连击)
                      G9 (社区订阅)
```

**关键变化对比 v1**：
- ✂️ 砍掉 4 个用户填写功能（F1/F3/F4/F6/F7/F9/F13/F14）= **0 用户填写动作**
- ➕ 新增 5 个零负担 AI feature（G0/G3/G4/G7/G8）
- 🎯 产品体验：上传 CSV → 看报告（G3）→ 提问（G7）→ 分享坏习惯账单（G4+F10）— 全程零文字输入

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

**报告字数**: ~6500 字 | **覆盖深度**: 文章 25 / KOL 12 / 大师 39 / 产品 14 | **v2 Feature**: 9 个零负担 G 系列 + 4 个保留 F 系列 = 13 个，按 ROI/Effort 排序

## 9. 设计公理速查表（v2 核心）

| 公理 | 含义 | 测试 |
|------|------|------|
| **用户事后 100% 记不得** | 散户没有事中记录的纪律。这是认知科学硬约束，不是 UX 问题 | 任何 feature 要求填字段 → 砍掉或改 AI 反推 |
| **零负担复盘** | 用户全程只需「上传 CSV → 看 → 提问」 | 用户输入动作 > 0 → 重设计 |
| **系统主动看见** | 用户看不见的行为模式，系统自动检测并标价 | G0 行为模式检测库是基石 |
| **AI 是数据采集层，不只是输出层** | LLM 不是用来生成花哨建议，而是用来反推用户没填的字段（thesis/setup/情绪） | LLM 应用先想"补什么数据"再想"输出什么" |
| **差异化 = post-mortem analyst，不是 journal** | 跟 Tradervue/Edgewonk/Tradezella/老唐范式划清界限 | 营销/PR 文案必须围绕这一点 |
