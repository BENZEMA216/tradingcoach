# TradingCoach — Product Hunt Launch Kit

Live: https://tradingcoach.vercel.app · Repo: https://github.com/BENZEMA216/tradingcoach
Status: Public Beta · CSV-only · not investment advice

---

## 1. Positioning (one sentence)

TradingCoach is a **trading post-mortem analyst**, not a trading journal. You don't log
anything — you upload one broker CSV and it shows you the behavior patterns your P&L hides
(revenge trading, persistent-loser symbols, cutting winners early), then back-tests what a
fix would have saved.

The wedge: every competitor (Tradervue, Edgewonk, TradeZella) is a *notebook* that needs
discipline. TradingCoach is an *analyst* that needs nothing but your trade history.

---

## 2. Name & Tagline

**Name:** TradingCoach

**Tagline options** (PH limit ~60 chars — all fit):
1. `Find the trading habits costing you money` *(recommended — matches the live hero)*
2. `Your trades, auto-analyzed. No journaling required.`
3. `The post-mortem analyst for your trading history`
4. `Upload one CSV. See the habits your P&L hides.`

---

## 3. Description (the "what is it" — ~260 chars)

> TradingCoach turns one broker CSV into a behavior post-mortem. No journaling, no manual
> tagging: it detects patterns like revenge trading and persistent-loser symbols, scores
> each trade, and back-tests what disciplined rules would have saved. Try the sample data —
> no signup.

---

## 4. Topics / Categories (pick 3)

`Fintech` · `Investing` · `Analytics` · `Productivity` (secondary)

---

## 5. Gallery (image order + captions)

Assets in `project_docs/ph_assets/` (2560×1600, retina). Recommended order:

1. **01-landing.png** — "Upload one CSV. No signup. Try the sample first."
2. **02-statistics.png** — "It found revenge trading and your strongest symbol — automatically."
3. **03-backtest.png** — "Counterfactual back-test: what a hard stop would have saved you."
4. **05-position-detail.png** — "Every trade scored on entry, exit, trend and risk."
5. **06-ai-coach.png** — "AI coach summarizes your problems and strengths."

First image is the scroll-stopper — lead with **02-statistics** if you want the big
−$18,841 + "Possible revenge trading" number in the thumbnail instead of the hero.

---

## 6. Maker's first comment (post immediately on launch)

> Hey hunters 👋
>
> I built TradingCoach because every trading journal I tried died the same way: they all
> assume you'll diligently log every trade. Nobody does. So the review never happens.
>
> TradingCoach flips it. You don't write anything — you export one CSV from your broker,
> drop it in, and it does the post-mortem for you: detects revenge trading, symbols that
> quietly bleed you, winners you cut too early; scores each trade; and back-tests what a
> simple rule (a hard stop, skipping a persistent loser) would have changed.
>
> It's a public beta and CSV-only right now (Futu first; more brokers coming — tell me
> yours). It is a review tool, not investment advice, and it never connects to your account.
>
> 👉 Try it with the sample data, no signup: https://tradingcoach.vercel.app
>
> Brutal feedback very welcome — there's a feedback button in-app that files a GitHub issue
> directly. What broker should I support next?

---

## 7. Demo video script (30–45s screen recording)

Record at 1280×800, English UI, the sample workspace. Beats:

- **0:00–0:05** Landing. Cursor clicks **Try Sample Data**. (VO/caption: "No signup. One click.")
- **0:05–0:14** Statistics loads. Slow-pan the −$18,841 P&L, then the insight cards.
  Caption: "It found revenge trading — and your best symbol — on its own."
- **0:14–0:24** Click into a position. Show the quality scores (entry/exit/trend/risk).
  Caption: "Every trade scored. No tagging."
- **0:24–0:36** Open Backtest. Expand "Hard stop-loss". Show +$27k and the dual line chart.
  Caption: "What would discipline have saved? Back-tested on your real trades."
- **0:36–0:43** Cut to upload screen. Caption: "Your CSV. Same in 10 seconds."
- **0:43–0:45** End card: logo + "tradingcoach.vercel.app · public beta".

Keep it silent-friendly (captions, no required voiceover). Export 1080p, <30MB for PH.

---

## 8. Comment FAQ (canned replies)

- **"Is my data safe?"** → CSV-only, no broker login, no account connection. Beta workspaces
  are anonymous and auto-delete after 72h. You can wipe yours instantly with "Delete workspace".
- **"Which brokers?"** → Futu (EN + CN) today. The importer is format-pluggable — drop your
  broker's CSV header in a feedback issue and I'll add it.
- **"Is this financial advice?"** → No. It's a review/analytics tool on your own history.
- **"Open source?"** → Yes, the repo is public (link above); feedback files a GitHub issue.
- **"Excel/xlsx?"** → Not yet — export to CSV for now.

---

## 9. Open items before launch

- **AI Coach** — resolved for beta: the unwired LLM Chat tab and "AI Unavailable" badge are
  hidden; the page is now rule-based Insights only, with a bilingual summary. If you later
  want the chat back, wire an LLM (OpenRouter-compatible) and re-enable the tab.
- **Custom domain**: currently on `tradingcoach.vercel.app` + Railway subdomain. Optional for
  launch; can swap later with no code change.
- **Demo video**: script is in §7; still needs an actual screen recording.

---

## 10. Launch logistics

- **When:** PH day starts 00:01 PT. Post the maker comment within the first minutes.
- **Hunter:** self-hunt is fine for a beta; a known hunter helps reach but isn't required.
- **First hour:** reply to every comment; pin the sample-data link.
- **Assets ready:** thumbnail (use 02-statistics crop), 5 gallery images, demo video, tagline,
  description, topics, maker comment — all above.
