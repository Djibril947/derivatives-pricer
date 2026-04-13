import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm
import yfinance as yf

# ── Téléchargement données S&P 500 ───────────────────
data = yf.download("^GSPC", start="2023-01-01", end="2024-01-01")
S_data = data['Close'].squeeze()

print(f"Données téléchargées : {len(S_data)} jours")
print(S_data.head())

# ── Paramètres de l'option ───────────────────────────
K = 4000       # Strike
r = 0.05       # Taux sans risque
sigma = 0.20   # Volatilité implicite fixe
T_total = 1    # Maturité 1 an

# ── Calcul du Delta BSM à chaque jour ────────────────
n = len(S_data)
t = np.linspace(0, T_total, n)  # temps écoulé
T_remaining = T_total - t        # temps restant

# Éviter division par zéro au dernier jour
T_remaining[-1] = 1e-6

d1 = (np.log(S_data.values / K) + (r + 0.5 * sigma**2) * T_remaining) / (sigma * np.sqrt(T_remaining))
delta = norm.cdf(d1)

# ── Simulation du delta hedging ──────────────────────
cash = np.zeros(n)
pnl  = np.zeros(n)

# Jour 0 : on vend le call, on achète delta actions
S0 = S_data.values[0]
T0 = T_remaining[0]
d1_0 = (np.log(S0 / K) + (r + 0.5 * sigma**2) * T0) / (sigma * np.sqrt(T0))
d2_0 = d1_0 - sigma * np.sqrt(T0)
call_price_0 = S0 * norm.cdf(d1_0) - K * np.exp(-r * T0) * norm.cdf(d2_0)

cash[0] = call_price_0 - delta[0] * S0  # prime reçue - actions achetées

# Rebalancement quotidien
for i in range(1, n):
    # Intérêts sur le cash
    cash[i] = cash[i-1] * np.exp(r / 365)
    # Ajustement du delta
    cash[i] -= (delta[i] - delta[i-1]) * S_data.values[i]

# P&L final = cash + actions - payoff du call
payoff_final = max(S_data.values[-1] - K, 0)
pnl_final = cash[-1] + delta[-1] * S_data.values[-1] - payoff_final

print(f"\n── Delta Hedging ────────────────────")
print(f"Prix call BSM initial  : {call_price_0:.2f}")
print(f"Payoff final du call   : {payoff_final:.2f}")
print(f"P&L du hedger          : {pnl_final:.2f}")
print(f"Erreur vs BSM          : {pnl_final - 0:.2f}")

# ── Graphique P&L cumulé ─────────────────────────────
pnl_daily = np.zeros(n)
for i in range(1, n):
    pnl_daily[i] = (cash[i] - cash[i-1]) - (delta[i] - delta[i-1]) * S_data.values[i]

pnl_cumul = np.cumsum(pnl_daily)

plt.figure(figsize=(12, 6))
plt.plot(S_data.index, pnl_cumul, color='steelblue', linewidth=2, label='P&L cumulé')
plt.axhline(y=0, color='red', linestyle='--', linewidth=1.5, label='P&L théorique = 0')
plt.title('Delta Hedging — P&L cumulé réalisé vs théorique')
plt.xlabel('Date')
plt.ylabel('P&L (points)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()