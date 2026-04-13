# Derivatives Pricer — Python

Black-Scholes pricing, Greeks, Monte-Carlo simulation and delta-hedging backtest on real S&P 500 data.

Built as part of an independent quantitative finance self-study programme alongside the DerivativesFinance training platform and *Options, Futures & Other Derivatives* (J.C. Hull).

---

## Projects

### 1. Black-Scholes Pricer (`Black scholes.py`)

Full implementation of the Black-Scholes-Merton model for European options.

**Pricing**
- Vanilla call & put using closed-form BSM formula

**Greeks — first order**
| Greek | Formula |
|-------|---------|
| Delta | N(d1) |
| Gamma | N'(d1) / (S·σ·√T) |
| Vega  | S·N'(d1)·√T / 100 |
| Theta | -(S·N'(d1)·σ)/(2√T) - rKe^(-rT)·N(d2) |
| Rho   | K·T·e^(-rT)·N(d2) / 100 |

**Greeks — second order**
| Greek | Description |
|-------|-------------|
| Vanna | Sensitivity of Delta to volatility — key for exotic hedging |
| Volga | Sensitivity of Vega to volatility (Vega convexity) — drives exotic pricing |

**Monte-Carlo simulation**
- 10,000 simulated paths of the underlying
- European option pricing via discounted average payoff
- Convergence analysis: MC price vs closed-form BSM across 10 to 50,000 simulations

---

### 2. Delta-Hedging Backtest (`hedging.py`)

Dynamic delta-hedging simulation on real S&P 500 data (2023).

**Methodology**
- Download 250 days of S&P 500 prices via `yfinance`
- Compute BSM delta at each trading day
- Simulate daily portfolio rebalancing: sell call, buy delta shares, earn risk-free rate on cash
- Track cumulative P&L vs theoretical P&L = 0

**Key result**
The backtest demonstrates that discrete daily rebalancing generates a non-zero P&L due to:
- Basis risk between implied volatility (σ = 20%) and realised volatility
- Unhedged gamma exposure between rebalancing dates

---

## Stack

## Run

```bash
python "Black scholes.py"
python hedging.py
```

## Author

Djibril DRAME — M1 Grande École, Grenoble Ecole de Management  
Self-directed training in quantitative finance & derivatives