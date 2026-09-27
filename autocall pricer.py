"""
Pricing d'un Phoenix Autocall par simulation Monte Carlo.
"""

import numpy as np


def simuler_trajectoires(S0, r, q, sigma, T, n_pas, n_trajectoires, seed=None, antithetic=True):
    """Simule des trajectoires GBM du sous-jacent (mouvement brownien géométrique)."""
    rng = np.random.default_rng(seed)
    dt = T / n_pas
    drift = (r - q - 0.5 * sigma**2) * dt
    vol = sigma * np.sqrt(dt)

    if antithetic:
        moitie = (n_trajectoires + 1) // 2
        z = rng.standard_normal((moitie, n_pas))
        z = np.concatenate([z, -z], axis=0)[:n_trajectoires]
    else:
        z = rng.standard_normal((n_trajectoires, n_pas))

    increments_log = drift + vol * z
    chemins_log = np.cumsum(increments_log, axis=1)
    chemins_log = np.concatenate([np.zeros((n_trajectoires, 1)), chemins_log], axis=1)

    return S0 * np.exp(chemins_log)


def prix_phoenix_autocall(
    S0, r, q, sigma, T,
    n_observations,
    barriere_rappel,
    barriere_coupon,
    barriere_protection,
    coupon,
    n_trajectoires=100_000,
    seed=42,
):
    """
    Price un Phoenix Autocall par Monte Carlo.
    Retourne (prix, erreur_std), prix exprimé en % du nominal (ex: 1.0145 = 101.45%).
    """
    S0_B_rappel = barriere_rappel * S0
    S0_B_coupon = barriere_coupon * S0
    S0_B_protec = barriere_protection * S0

    chemins = simuler_trajectoires(S0, r, q, sigma, T, n_observations, n_trajectoires, seed)
    obs = chemins[:, 1:]

    n = n_trajectoires
    dt_obs = T / n_observations

    memoire_coupon = np.zeros(n)
    payoffs = np.zeros(n)
    temps_remboursement = np.full(n, T)
    deja_rappele = np.zeros(n, dtype=bool)

    for i in range(n_observations):
        S_i = obs[:, i]
        t_i = (i + 1) * dt_obs

        actifs = ~deja_rappele

        touche_coupon = actifs & (S_i >= S0_B_coupon)
        memoire_coupon[touche_coupon] += coupon

        rappele_ce_jour = actifs & (S_i >= S0_B_rappel)
        payoffs[rappele_ce_jour] = 1.0 + memoire_coupon[rappele_ce_jour]
        temps_remboursement[rappele_ce_jour] = t_i
        deja_rappele |= rappele_ce_jour

    jamais_rappele = ~deja_rappele
    S_T = obs[:, -1]

    au_dessus_protec = jamais_rappele & (S_T >= S0_B_protec)
    payoffs[au_dessus_protec] = 1.0 + memoire_coupon[au_dessus_protec]

    en_dessous_protec = jamais_rappele & (S_T < S0_B_protec)
    payoffs[en_dessous_protec] = S_T[en_dessous_protec] / S0

    payoffs_actualises = payoffs * np.exp(-r * temps_remboursement)

    prix = payoffs_actualises.mean()
    erreur_std = payoffs_actualises.std(ddof=1) / np.sqrt(n)

    return prix, erreur_std


if __name__ == "__main__":
    # -- Test 1 : cas de base --
    prix, err = prix_phoenix_autocall(
        S0=100, r=0.03, q=0.0, sigma=0.20, T=3.0,
        n_observations=12,
        barriere_rappel=1.00,
        barriere_coupon=0.70,
        barriere_protection=0.60,
        coupon=0.02,
    )
    print(f"Prix (en % du nominal) = {prix*100:.2f}%")
    print(f"Intervalle 95% ≈ ±{1.96*err*100:.2f}%")

    # -- Test 2 : sensibilité au coupon --
    print("\n=== Phoenix Autocall — sensibilité au coupon ===\n")
    for coupon in [0.01, 0.02, 0.03, 0.04]:
        prix, err = prix_phoenix_autocall(
            S0=100, r=0.03, q=0.0, sigma=0.20, T=3.0,
            n_observations=12,
            barriere_rappel=1.00,
            barriere_coupon=0.70,
            barriere_protection=0.60,
            coupon=coupon,
        )
        print(f"Coupon {coupon*100:.0f}% par trimestre -> Prix = {prix*100:.2f}%  (±{1.96*err*100:.2f}%)")