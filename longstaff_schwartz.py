import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

# Paramètres — Put Américain
S = 100      # Prix actuel du sous-jacent
K = 110      # Strike — on met 110 pour avoir un put in-the-money
T = 1        # Maturité 1 an
r = 0.05     # Taux sans risque
sigma = 0.20 # Volatilité
N = 10000    # Nombre de trajectoires
steps = 50   # Dates d'exercice possibles
dt = T / steps  # pas de temps entre chaque date

# ── Simulation des trajectoires ──────────────────────
np.random.seed(42)

# Matrice de prix : N trajectoires × (steps+1) dates
S_paths = np.zeros((N, steps + 1))
S_paths[:, 0] = S

for t in range(1, steps + 1):
    Z = np.random.standard_normal(N)
    S_paths[:, t] = S_paths[:, t-1] * np.exp( (r - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z )

print(f"Trajectoires simulées : {S_paths.shape}")
print(f"Prix initial   : {S_paths[0, 0]:.2f}")
print(f"Exemple prix final trajectoire 1 : {S_paths[0, -1]:.2f}")

# ── Payoff du put à chaque date ──────────────────────
# max(K - S, 0) pour chaque trajectoire à chaque step
payoff = np.maximum(K - S_paths, 0)

print(f"Payoff max possible    : {payoff.max():.2f}")
print(f"Payoff moyen à maturité: {payoff[:, -1].mean():.2f}")

# ── Backward Induction — Longstaff-Schwartz ──────────
# On part de la maturité et on remonte vers t=0

# Cash flows optimaux — initialisés avec le payoff à maturité
cash_flows = payoff[:, -1].copy()

# On remonte de t=49 jusqu'à t=1
for t in range(steps - 1, 0, -1):

    # 1 — Trajectoires in the money à la date t
    itm = payoff[:, t] > 0
    
    if itm.sum() == 0:
        continue

    # 2 — Régression : continuation value ~ f(S)
    # X = prix du sous-jacent pour les trajectoires ITM
    # Y = cash flows futurs actualisés
    X = S_paths[itm, t]
    Y = cash_flows[itm] * np.exp(-r * dt)

    # Régression polynomiale ordre 2 (comme Longstaff-Schwartz original)
    coeffs = np.polyfit(X, Y, 2)
    continuation = np.polyval(coeffs, X)

    # 3 — Règle d'exercice optimal
    # Si payoff immédiat > continuation value → on exerce
    exercise = payoff[itm, t] > continuation
    
    # Mise à jour des cash flows
    cash_flows[itm] = np.where(
        exercise,
        payoff[itm, t],           # on exerce → payoff immédiat
        cash_flows[itm] * np.exp(-r * dt)  # on attend → on actualise
    )

# ── Prix final ────────────────────────────────────────
price_ls = np.exp(-r * dt) * np.mean(cash_flows)

print(f"\n── Longstaff-Schwartz ───────────────────")
print(f"Prix Put Américain (LS)  : {price_ls:.4f}")
# ── Comparaison BSM européen vs LS américain ─────────
d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
d2 = d1 - sigma*np.sqrt(T)
put_european = K*np.exp(-r*T)*norm.cdf(-d2) - S*norm.cdf(-d1)

print(f"Prix Put Européen (BSM)  : {put_european:.4f}")
print(f"Prix Put Américain (LS)  : {price_ls:.4f}")
print(f"Prime exercice anticipé  : {price_ls - put_european:.4f}")
print(f"Ratio américain/européen : {price_ls/put_european:.4f}")
# ── Graphique — trajectoires + points d'exercice ─────
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# ── Graphique 1 : trajectoires + exercice optimal ────
exercise_points_x = []  # dates d'exercice
exercise_points_y = []  # prix au moment de l'exercice

# On re-simule la décision d'exercice pour trouver les points
cash_flows2 = payoff[:, -1].copy()
exercise_date = np.full(N, steps)  # par défaut exercice à maturité

for t in range(steps - 1, 0, -1):
    itm = payoff[:, t] > 0
    if itm.sum() == 0:
        continue
    X = S_paths[itm, t]
    Y = cash_flows2[itm] * np.exp(-r * dt)
    coeffs = np.polyfit(X, Y, 2)
    continuation = np.polyval(coeffs, X)
    exercise = payoff[itm, t] > continuation
    idx = np.where(itm)[0][exercise]
    exercise_date[idx] = t
    cash_flows2[itm] = np.where(
        exercise,
        payoff[itm, t],
        cash_flows2[itm] * np.exp(-r * dt)
    )

# Afficher 100 trajectoires
for i in range(100):
    ax1.plot(S_paths[i], color='gray', alpha=0.08, linewidth=0.5)

# Points d'exercice anticipé (avant maturité)
for i in range(N):
    if exercise_date[i] < steps:
        exercise_points_x.append(exercise_date[i])
        exercise_points_y.append(S_paths[i, exercise_date[i]])

ax1.scatter(exercise_points_x, exercise_points_y,
            color='red', s=3, alpha=0.3, label='Exercice anticipé', zorder=5)
ax1.axhline(y=K, color='blue', linestyle='--', linewidth=1.5, label=f'Strike K={K}')
ax1.set_title('Longstaff-Schwartz — Trajectoires et points d\'exercice optimal')
ax1.set_xlabel('Steps')
ax1.set_ylabel('Prix du sous-jacent')
ax1.legend()
ax1.grid(True, alpha=0.2)

# ── Graphique 2 : distribution des payoffs ────────────
payoffs_final = np.maximum(K - S_paths[np.arange(N), exercise_date], 0)
payoffs_final = payoffs_final[payoffs_final > 0]

ax2.hist(payoffs_final, bins=50, color='steelblue', alpha=0.8, edgecolor='none')
ax2.axvline(x=price_ls, color='red', linestyle='--',
            linewidth=2, label=f'Prix LS = {price_ls:.2f}')
ax2.axvline(x=put_european, color='orange', linestyle='--',
            linewidth=2, label=f'Prix BSM = {put_european:.2f}')
ax2.set_title('Distribution des payoffs — Put Américain')
ax2.set_xlabel('Payoff')
ax2.set_ylabel('Fréquence')
ax2.legend()
ax2.grid(True, alpha=0.2)

plt.tight_layout()
plt.show()