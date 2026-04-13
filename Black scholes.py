# importation des bibliotèques nécessairee
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm

# ── Paramètres
S = 100    # Prix actuel du sous-jacent
K = 100    # Strike (prix d'exercice)
T = 1      # Maturité en années (1 an)
r = 0.05   # Taux sans risque (5%)
sigma = 0.2  # Volatilité (20%)

# -- Formule Black-Scholes

d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
d2 = d1 - sigma * np.sqrt(T)

#-- Pricing --------------------

call = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
put  = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


#-- Greeks --------------------

delta_call = norm.cdf(d1)
delta_put  = norm.cdf(d1) - 1

gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))

vega  = S * norm.pdf(d1) * np.sqrt(T) / 100  # divisé par 100 → variation pour 1% de vol

theta_call = (- (S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
              - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
theta_put = (- (S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
             + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365

rho_call = K * T * np.exp(-r * T) * norm.cdf(d2) / 100  # pour 1% de taux
rho_put = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100

vanna = -norm.pdf(d1) * d2 / sigma 
volga = vega * (d1 * d2) / sigma

print(f"\n-- Pricing --------------------")
print(f"Call : {call:.2f}")
print(f"Put  : {put:.2f}")
print(f"\n-- Greeks --------------------")
print(f"Delta call : {delta_call:.4f}")
print(f"Delta put  : {delta_put:.4f}")
print(f"Gamma      : {gamma:.4f}")
print(f"Vega       : {vega:.4f}")
print(f"Theta call : {theta_call:.4f}")
print(f"Theta put  : {theta_put:.4f}")
print(f"Rho call   : {rho_call:.4f}")
print(f"Rho put    : {rho_put:.4f}")
print(f"Vanna     : {vanna:.4f}")
print(f"Volga   : {volga:.4f}")

# ── Monte-Carlo ──────────────────────────────────────
np.random.seed(42)      # pour reproduire les mêmes résultats
N = 10000               # nombre de simulations
dt = T                  # un seul pas de temps (maturité)

# Simulation des trajectoires
Z = np.random.standard_normal(N)
ST = S * np.exp((r - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z)

# Calcul des payoffs
payoff_call = np.maximum(ST - K, 0)
payoff_put  = np.maximum(K - ST, 0)

# Prix actualisés
call_mc = np.exp(-r * T) * np.mean(payoff_call)
put_mc  = np.exp(-r * T) * np.mean(payoff_put)

print(f"\n-- Monte-Carlo ({N} simulations) ----")
print(f"Call MC : {call_mc:.2f}  |  Call BSM : {call:.2f}")
print(f"Put  MC : {put_mc:.2f}  |  Put  BSM : {put:.2f}")

# ── Visualisation des trajectoires ───────────────────
steps = 252  # nombre de jours de trading dans un an
dt_daily = T / steps

# Simulation de 10000 trajectoires jour par jour
Z_path = np.random.standard_normal((N, steps))
ST_path = np.zeros((N, steps + 1))
ST_path[:, 0] = S

for t in range(steps):
    ST_path[:, t+1] = ST_path[:, t] * np.exp(
        (r - 0.5 * sigma**2) * dt_daily + sigma * np.sqrt(dt_daily) * Z_path[:, t]
    )

# Graphique
plt.figure(figsize=(12, 6))

# 200 trajectoires en gris transparent pour pas surcharger
for i in range(200):
    plt.plot(ST_path[i], color='grey', alpha=0.05, linewidth=0.5)

# Moyenne des trajectoires en rouge
plt.plot(ST_path.mean(axis=0), color='red', linewidth=2, label='Moyenne')

# Strike en pointillés
plt.axhline(y=K, color='red', linestyle='--', linewidth=1.5, label=f'Strike K={K}')

plt.title('Monte-Carlo — 10 000 trajectoires du sous-jacent')
plt.xlabel('Jours')
plt.ylabel('Prix du sous-jacent')
plt.legend()
plt.tight_layout()
plt.show()

# ── Convergence Monte-Carlo ──────────────────────────
simulations = [10, 50, 100, 500, 1000, 5000, 10000, 50000]
prix_mc = []

for n in simulations:
    Z = np.random.standard_normal(n)
    ST_conv = S * np.exp((r - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * Z)
    payoff = np.maximum(ST_conv - K, 0)
    prix_mc.append(np.exp(-r * T) * np.mean(payoff))

plt.figure(figsize=(12, 6))
plt.plot(simulations, prix_mc, color='steelblue', marker='o', linewidth=2, label='Prix Monte-Carlo')
plt.axhline(y=call, color='red', linestyle='--', linewidth=2, label=f'Prix BSM = {call:.2f}')
plt.xscale('log')
plt.title('Convergence Monte-Carlo vers Black-Scholes')
plt.xlabel('Nombre de simulations (échelle log)')
plt.ylabel('Prix du call')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
