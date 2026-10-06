# Black-Scholes Pricer in VBA

Note: Windows may block macros in downloaded files. Right-click the .xlsm file,
choose Properties, tick "Unblock", then reopen it. The full code is also readable
in BlackScholes_v4.bas.

A European option pricer (call and put) in Excel VBA: prices, Greeks (including Vanna and Volga) and implied volatility via Newton-Raphson. The functions work directly in cells, like native Excel formulas.

Results were validated against an equivalent Python library (see below).

## Repository contents

| File | Purpose |
|---|---|
| `BlackScholes_v4.bas` | The full VBA code (module to import) |
| `Pricer_BlackScholes.xlsm` | Demo workbook (inputs, results, implied volatility button) |
| `README.md` | This file |

## Usage

**Option 1: open the workbook.** Open `Pricer_BlackScholes.xlsm` and click "Enable Content" if Excel shows a macro warning.

**Option 2: import the code into your own workbook.**
1. Save the workbook as `.xlsm`.
2. Press `Alt + F11` to open the VBA editor.
3. Right-click the workbook in the project explorer, choose `Import File...` and select `BlackScholes_v4.bas`.
4. The functions are now available in cells.

Example:

```
=BS_Call(100,100,1,0.05,0.2)    → 10.4506
```

(Use semicolons as argument separators if your Excel is set to a European locale.)

## Common parameters

| Parameter | Meaning |
|---|---|
| `S` | Spot price of the underlying |
| `K` | Strike |
| `T` | Time to maturity in years |
| `r` | Annual risk-free rate (e.g. 0.05) |
| `sigma` | Annual volatility (e.g. 0.2) |

The functions reject `S`, `K`, `T` or `sigma` less than or equal to 0 and return `#VALUE!`.

## Functions

**Prices:** `BS_Call`, `BS_Put`

**Greeks:** `BS_Delta_Call`, `BS_Delta_Put`, `BS_Gamma`, `BS_Vega`, `BS_Theta_Call`, `BS_Theta_Put`, `BS_Rho_Call`, `BS_Rho_Put`, `BS_Vanna`, `BS_Volga`

**Implied volatility** (Newton-Raphson): `BS_ImpliedVol_Call(S, K, T, r, prixMarche)` and `BS_ImpliedVol_Put(S, K, T, r, prixMarche)`, where `prixMarche` is the observed market price.

**Helper functions:** `BS_N` (cumulative normal), `BS_Phi` (normal density), `BS_D1`, `BS_D2`. Input validation is written once in `BS_D1`, and every other function relies on it.

**Interface:** the `Calculer_VolImplicite` macro reads the market price (`B8`) and the option type Call/Put (`B9`) from the sheet, then writes the implied volatility to `B10`. An error message appears if the price is out of bounds.

## Conventions

| Greek | Unit |
|---|---|
| Vega | per volatility point (raw value divided by 100) |
| Theta | per calendar day (annual value divided by 365) |
| Rho | per interest rate point (raw value divided by 100) |
| Gamma, Delta, Vanna | raw value |
| Volga | computed from vega per volatility point |

## Validation

Inputs: S = 100, K = 100, T = 1, r = 5%, sigma = 20%. VBA values are compared with the Python library.

| Quantity | Call (VBA) | Put (VBA) | Python (call / put) |
|---|---|---|---|
| Price | 10.4506 | 5.5735 | 10.45 / 5.57 |
| Delta | 0.6368 | -0.3632 | 0.6368 / -0.3632 |
| Gamma | 0.0188 | 0.0188 | 0.0188 |
| Vega | 0.3752 | 0.3752 | 0.3752 |
| Theta | -0.0176 | -0.0045 | -0.0176 / -0.0045 |
| Rho | 0.5323 | -0.4189 | 0.5323 / -0.4189 |
| Vanna | -0.2814 | -0.2814 | -0.2814 |
| Volga | 0.0985 | 0.0985 | 0.0985 |

Consistency checks:
- Put-call parity: C − P = S − K·e^(−rT) = 4.8771.
- Call delta − put delta = 1.
- Call theta − put theta = −r·K·e^(−rT) / 365.
- Call rho − put rho = K·T·e^(−rT) / 100.
- A call at 10.4506 and a put at 5.5735 return the same implied volatility (20%).

## Implied volatility

Newton-Raphson adjusts the volatility until the model price matches the market price:

`sigma_new = sigma - (model_price - market_price) / vega`

It starts from sigma = 20%, stops when the price gap falls below 0.000001, and is capped at 100 iterations. The function raises an error if the market price is out of bounds (below the discounted intrinsic value or above the theoretical maximum), if vega is almost zero, or if the method does not converge.

Example: a call priced at 8 (S = K = 100, T = 1, r = 5%) gives an implied volatility of 13.38%.

## Limitations

- European options only.
- No dividends; constant rate and volatility.
- Implied volatility is only as precise as the rounding of the market price.
- Newton-Raphson can fail for deep out-of-the-money options (very low vega).
