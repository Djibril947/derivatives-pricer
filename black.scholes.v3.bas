Attribute VB_Name = "Module1"
Option Explicit

' N(x) : probabilité cumulée de la loi normale centrée réduite
Function BS_N(x As Double) As Double
    BS_N = Application.WorksheetFunction.Norm_S_Dist(x, True)
End Function
' d1 de Black-Scholes, avec contrôle des inputs (S, K, T, sigma doivent être > 0)
Function BS_D1(S As Double, K As Double, T As Double, r As Double, sigma As Double) As Double

    If S <= 0 Or K <= 0 Or T <= 0 Or sigma <= 0 Then
        Err.Raise 5, , "Inputs invalides : S, K, T et sigma doivent être > 0"
    End If

    BS_D1 = (Log(S / K) + (r + sigma ^ 2 / 2) * T) / (sigma * Sqr(T))

End Function

' d2 = d1 - sigma * racine de T
' Le contrôle des inputs est déjà fait dans BS_D1.
Function BS_D2(S As Double, K As Double, T As Double, r As Double, sigma As Double) As Double
    
    BS_D2 = BS_D1(S, K, T, r, sigma) - sigma * Sqr(T)

End Function
' Prix d'un call européen : S*N(d1) - K*e^(-rT)*N(d2)
Function BS_Call(S As Double, K As Double, T As Double, r As Double, sigma As Double) As Double

    Dim Nd1 As Double
    Dim Nd2 As Double

    Nd1 = BS_N(BS_D1(S, K, T, r, sigma))
    Nd2 = BS_N(BS_D2(S, K, T, r, sigma))

    BS_Call = S * Nd1 - K * Exp(-r * T) * Nd2

End Function

' Prix d'un put européen : K*e^(-rT)*N(-d2) - S*N(-d1)
Function BS_Put(S As Double, K As Double, T As Double, r As Double, sigma As Double) As Double

    Dim Nmd1 As Double
    Dim Nmd2 As Double

    Nmd1 = BS_N(-BS_D1(S, K, T, r, sigma))
    Nmd2 = BS_N(-BS_D2(S, K, T, r, sigma))

    BS_Put = K * Exp(-r * T) * Nmd2 - S * Nmd1

End Function

' Delta d'un call européen : N(d1), compris entre 0 et 1
Function BS_Delta_Call(S As Double, K As Double, T As Double, r As Double, sigma As Double) As Double
    
    BS_Delta_Call = BS_N(BS_D1(S, K, T, r, sigma))

End Function
 
' Delta d'un put européen : N(d1)- 1 , compris entre -1 et 0
Function BS_Delta_Put(S As Double, K As Double, T As Double, r As Double, sigma As Double) As Double
    
    BS_Delta_Put = BS_N(BS_D1(S, K, T, r, sigma)) - 1

End Function

' phi(x) : densité de la loi normale centrée réduite
Function BS_Phi(x As Double) As Double
    
    BS_Phi = Application.WorksheetFunction.Norm_S_Dist(x, False)

End Function

' Gamma (identique pour call et put) : phi(d1) / (S * sigma * racine de T)
Function BS_Gamma(S As Double, K As Double, T As Double, r As Double, sigma As Double) As Double

    BS_Gamma = BS_Phi(BS_D1(S, K, T, r, sigma)) / (S * sigma * Sqr(T))
    
End Function

' Vega (identique pour call et put) : S * phi(d1) * racine de T / 100
Function BS_Vega(S As Double, K As Double, T As Double, r As Double, sigma As Double) As Double

    BS_Vega = S * BS_Phi(BS_D1(S, K, T, r, sigma)) * Sqr(T) / 100

End Function

' Theta call par jour (différent du put) : -( S * phi(d1) * sigma / (2 * racine de T)) - r * K* e^(- r * T) * N(d2)
Function BS_Theta_Call(S As Double, K As Double, T As Double, r As Double, sigma As Double) As Double

    Dim A1 As Double
    Dim A2 As Double

    A1 = -(S * BS_Phi(BS_D1(S, K, T, r, sigma)) * sigma / (2 * Sqr(T)))
    A2 = -r * K * Exp(-r * T) * BS_N(BS_D2(S, K, T, r, sigma))

    BS_Theta_Call = (A1 + A2) / 365

End Function
' Theta put par jour : (-S*phi(d1)*sigma/(2*racine de T) + r*K*e^(-rT)*N(-d2)) / 365
Function BS_Theta_Put(S As Double, K As Double, T As Double, r As Double, sigma As Double) As Double

    Dim A1 As Double
    Dim A2 As Double

    A1 = -(S * BS_Phi(BS_D1(S, K, T, r, sigma)) * sigma / (2 * Sqr(T)))
    A2 = r * K * Exp(-r * T) * BS_N(-BS_D2(S, K, T, r, sigma))

    BS_Theta_Put = (A1 + A2) / 365

End Function
' Rho call par point de taux (différent du Put) : K * T * e^(- r * T) * N(d2)
Function BS_Rho_Call(S As Double, K As Double, T As Double, r As Double, sigma As Double) As Double

    BS_Rho_Call = (K * T * Exp(-r * T) * BS_N(BS_D2(S, K, T, r, sigma))) / 100

End Function
' Rho put par point de taux (différent du Call) : -K * T * e^(- r * T) * N(-d2)
Function BS_Rho_Put(S As Double, K As Double, T As Double, r As Double, sigma As Double) As Double

    BS_Rho_Put = -(K * T * Exp(-r * T) * BS_N(-BS_D2(S, K, T, r, sigma))) / 100

End Function

' Vanna (identique pour call et put) : -phi(d1) * d2 / sigma
Function BS_Vanna(S As Double, K As Double, T As Double, r As Double, sigma As Double) As Double

   BS_Vanna = -BS_Phi(BS_D1(S, K, T, r, sigma)) * BS_D2(S, K, T, r, sigma) / sigma

End Function

' Volga (identique pour call et put) : Vega * d1 * d2 / sigma
Function BS_Volga(S As Double, K As Double, T As Double, r As Double, sigma As Double) As Double

    BS_Volga = BS_Vega(S, K, T, r, sigma) * BS_D1(S, K, T, r, sigma) * BS_D2(S, K, T, r, sigma) / sigma

End Function

'' Volatilité implicite d'un call par Newton-Raphson
Function BS_ImpliedVol_Call(S As Double, K As Double, T As Double, r As Double, prixMarche As Double) As Double

    Dim sigma As Double
    Dim ecart As Double
    Dim vega As Double
    Dim prixMin As Double
    Dim i As Integer

    ' Un call vaut au minimum sa valeur intrinsèque actualisée, et au maximum S
    prixMin = S - K * Exp(-r * T)
    If prixMin < 0 Then prixMin = 0

    If prixMarche <= prixMin Or prixMarche >= S Then
        Err.Raise 5, , "Prix de marché hors bornes : aucune vol implicite"
    End If

    sigma = 0.2

    For i = 1 To 100

        ecart = BS_Call(S, K, T, r, sigma) - prixMarche

        If Abs(ecart) < 0.000001 Then
            BS_ImpliedVol_Call = sigma
            Exit Function
        End If

        vega = BS_Vega(S, K, T, r, sigma) * 100

        ' Vega quasi nul : la correction serait absurde
        If vega < 0.00000001 Then
            Err.Raise 5, , "Vega trop faible : pas de convergence"
        End If

        sigma = sigma - ecart / vega

        ' Évite une vol négative ou nulle au tour suivant
        If sigma < 0.0001 Then sigma = 0.0001

    Next i

    Err.Raise 5, , "Pas de convergence après 100 itérations"

End Function
' Volatilité implicite d'un put par Newton-Raphson
Function BS_ImpliedVol_Put(S As Double, K As Double, T As Double, r As Double, prixMarche As Double) As Double

    Dim sigma As Double
    Dim ecart As Double
    Dim vega As Double
    Dim prixMin As Double
    Dim i As Integer

    ' Un put vaut au minimum sa valeur intrinsèque actualisée, et au maximum K * e^(-rT)
    prixMin = K * Exp(-r * T) - S
    If prixMin < 0 Then prixMin = 0

    If prixMarche <= prixMin Or prixMarche >= K * Exp(-r * T) Then
        Err.Raise 5, , "Prix de marché hors bornes : aucune vol implicite"
    End If

    sigma = 0.2

    For i = 1 To 100

        ecart = BS_Put(S, K, T, r, sigma) - prixMarche

        If Abs(ecart) < 0.000001 Then
            BS_ImpliedVol_Put = sigma
            Exit Function
        End If

        vega = BS_Vega(S, K, T, r, sigma) * 100

        ' Vega quasi nul : la correction serait absurde
        If vega < 0.00000001 Then
            Err.Raise 5, , "Vega trop faible : pas de convergence"
        End If

        sigma = sigma - ecart / vega

        ' Évite une vol négative ou nulle au tour suivant
        If sigma < 0.0001 Then sigma = 0.0001

    Next i

    Err.Raise 5, , "Pas de convergence après 100 itérations"

End Function
