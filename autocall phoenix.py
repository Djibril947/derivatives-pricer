"""
Pricing d'un Phoenix Autocall par simulation Monte Carlo.

Principe du produit :
- A chaque date d'observation, si le sous-jacent est >= barrière de coupon, un coupon est versé.
- Si le sous-jacent est >= barrière de rappel, le produit est remboursé par anticipation
  (le capital est rendu et le produit s'arrête).
- A maturité, si le produit n'a jamais été rappelé :
    * sous-jacent >= barrière de protection -> le capital est rendu en entier
    * sous-jacent <  barrière de protection -> le client perd du capital (il récupère S_T / S0)
"""

import numpy as np


def simuler_trajectoires(S0, r, q, sigma, T, n_pas, n_trajectoires, seed=None, antithetic=True):
    """Simule des trajectoires GBM du sous-jacent (mouvement brownien géométrique)."""

    rng = np.random.default_rng(seed)      # générateur aléatoire (seed fixe = résultats reproductibles)
    dt = T / n_pas                         # durée d'un pas de temps (en années)
    drift = (r - q - 0.5 * sigma**2) * dt  # partie déterministe de l'évolution du log du prix
    vol = sigma * np.sqrt(dt)              # écart-type du choc aléatoire sur un pas

    if antithetic:
        # Variables antithétiques : pour chaque tirage z, on utilise aussi -z.
        # Cela réduit la variance de l'estimation (résultat plus précis à nombre égal de tirages).
        moitie = (n_trajectoires + 1) // 2
        z = rng.standard_normal((moitie, n_pas))
        z = np.concatenate([z, -z], axis=0)[:n_trajectoires]
    else:
        z = rng.standard_normal((n_trajectoires, n_pas))

    increments_log = drift + vol * z                 # variation du log-prix à chaque pas
    chemins_log = np.cumsum(increments_log, axis=1)  # cumul -> log(S_t / S0) à chaque date
    # On ajoute une colonne de zéros au début : à t = 0, log(S0 / S0) = 0
    chemins_log = np.concatenate([np.zeros((n_trajectoires, 1)), chemins_log], axis=1)

    return S0 * np.exp(chemins_log)                  # on revient aux prix : S_t = S0 * exp(...)


def prix_phoenix_autocall(S0, r, q, sigma, T, n_observations, barriere_rappel, barriere_coupon, barriere_protection, coupon, n_trajectoires=100_000, seed=42,):
    """
    Price un Phoenix Autocall par Monte Carlo.
    Retourne (prix, erreur_std), prix exprimé en % du nominal (ex: 1.0195 = 101.95%).
    """

    # Les barrières sont données en % de S0 (ex: 0.70), on les convertit en niveaux de prix
    S0_B_rappel = barriere_rappel * S0
    S0_B_coupon = barriere_coupon * S0
    S0_B_protec = barriere_protection * S0

    # On simule toutes les trajectoires, une date d'observation par pas
    chemins = simuler_trajectoires(S0, r, q, sigma, T, n_observations, n_trajectoires, seed)
    obs = chemins[:, 1:]          # on enlève la colonne t=0 : il ne reste que les dates d'observation

    n = n_trajectoires
    dt_obs = T / n_observations   # temps entre deux observations

    # pv[k] = valeur actuelle de tout ce que touche l'investisseur sur la trajectoire k
    pv = np.zeros(n)
    # deja_rappele[k] = True si le produit s'est déjà arrêté (rappel anticipé) sur la trajectoire k
    deja_rappele = np.zeros(n, dtype=bool)

    for i in range(n_observations):
        S_i = obs[:, i]                  # prix du sous-jacent à la date i, pour toutes les trajectoires
        t_i = (i + 1) * dt_obs           # date d'observation en années
        actifs = ~deja_rappele           # trajectoires où le produit est encore vivant

        # 1) Coupon : versé à CETTE date si le sous-jacent est >= barrière de coupon.
        #    On l'actualise tout de suite à t_i (c'est à cette date qu'il est payé).
        touche_coupon = actifs & (S_i >= S0_B_coupon)
        pv[touche_coupon] += coupon * np.exp(-r * t_i)

        # 2) Rappel anticipé : si S >= barrière de rappel, le capital est rendu à t_i
        #    et le produit s'arrête pour cette trajectoire.
        rappele = actifs & (S_i >= S0_B_rappel)
        pv[rappele] += np.exp(-r * t_i)
        deja_rappele |= rappele          # on marque ces trajectoires comme terminées

    # --- Remboursement à maturité pour les trajectoires jamais rappelées ---
    jamais_rappele = ~deja_rappele
    S_T = obs[:, -1]                     # prix final du sous-jacent

    # Capital rendu à maturité :
    #   - 1.0 (100 %) si S_T >= barrière de protection
    #   - S_T / S0 sinon (le client subit la baisse du sous-jacent)
    capital = np.where(S_T >= S0_B_protec, 1.0, S_T / S0)
    pv[jamais_rappele] += capital[jamais_rappele] * np.exp(-r * T)

    # Prix = moyenne des valeurs actuelles sur toutes les trajectoires
    prix = pv.mean()
    # Erreur standard de l'estimation Monte Carlo (sert à construire l'intervalle de confiance)
    erreur_std = pv.std(ddof=1) / np.sqrt(n)

    return prix, erreur_std


if __name__ == "__main__":
    # -- Test 1 : cas de base --
    prix, err = prix_phoenix_autocall(
        S0=100, r=0.03, q=0.0, sigma=0.20, T=3.0,
        n_observations=12,        # une observation par trimestre sur 3 ans
        barriere_rappel=1.00,     # rappel si S >= 100 % de S0
        barriere_coupon=0.70,     # coupon versé si S >= 70 % de S0
        barriere_protection=0.60, # capital protégé à maturité si S >= 60 % de S0
        coupon=0.02,              # 2 % par trimestre
    )
    print(f"Prix (en % du nominal) = {prix*100:.2f}%")
    print(f"Intervalle 95% ≈ ±{1.96*err*100:.2f}%")

    # -- Test 2 : sensibilité au coupon --
    print("\n=== Phoenix Autocall — sensibilité au coupon ===\n")
    for coupon in [0.01, 0.02, 0.03, 0.04]:
        prix, err = prix_phoenix_autocall(
            S0=100, r=0.03, q=0.0, sigma=0.20, T=3.0, n_observations=12, barriere_rappel=1.00, barriere_coupon=0.70, barriere_protection=0.60, coupon=coupon)
        print(f"Coupon {coupon*100:.0f}% par trimestre -> Prix = {prix*100:.2f}%  (±{1.96*err*100:.2f}%)")