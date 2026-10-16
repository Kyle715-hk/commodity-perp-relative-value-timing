# Gold Relative Value & Oil Timing on Commodity Perpetuals

Quantitative research project: **same-exchange gold relative value** and **oil timing augmentation** on Gate.io perpetual contracts.

Built under a faculty-supervised quant research program (HKU Business School). Focus: signal design, transaction costs, funding, exposure control, and reproducible frozen delivery.

## Strategies

| Strategy | Type | Instruments | Benchmark |
|----------|------|-------------|-----------|
| `gold_rv_v5_full` | Relative value | PAXG_USDT, XAUT_USDT | Zero (market-neutral pair) |
| `oil_timing_v3` | Timing | CL_USDT | Buy-and-hold excess vs CL |

### Gold relative value
- Daily z-score mean-reversion on log spread with rolling hedge ratio  
- Gross exposure capped at 1.0; decisions at most once per day  
- **Process metrics (after costs):** turnover ≈ 10 · fees ≈ $49 / $10k · max drawdown ≈ 0.5%  

### Oil timing
- Vol-normalized trend + funding tilt; position cap + rebalance cooldown  
- Evaluated on excess return vs continuous CL buy-and-hold  
- **Process metrics (after costs):** turnover ≈ 8 · fees ≈ $39 / $10k · tight absolute drawdown control  

> Absolute gold return was near flat on the reported window. The frozen design prioritizes **cost stability and risk control** after high-turnover prototypes failed fee stress tests.

## What this demonstrates
- End-to-end quant workflow: topic freeze → data QA → hypothesis tests → cost stress → frozen package  
- Practical handling of fees, funding, turnover, and exposure rules  
- Documentation of unsuccessful high-churn variants  
- Reproducible `strategy.py` / `strategy.json` delivery  

## Repository layout
```text
strategies/gold_rv_v5_full/
strategies/oil_timing_v3/
report/Stream_3_Final_Report.pdf
results/.../summary.json


Limitations

Gold: limited alpha after costs on the sample; value is process and cost discipline
Oil: shorter contract history; excess drawdown vs buy-and-hold is a known constraint
Engine/data access follows program tooling; this repo does not redistribute proprietary toolkit binaries or licensed tick data

Author
Kyle Chan · BASc Social Data Science, HKU

LinkedIn: linkedin.com/in/wang-tik-chan

Email: wangtikchan715@gmail.com
