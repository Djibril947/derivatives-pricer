
import numpy as np

N = 1000000  # nombre de points tirés

x = np.random.uniform(-1, 1, N)  # coordonnées x aléatoires
y = np.random.uniform(-1, 1, N)  # coordonnées y aléatoires

dans_cercle = x**2 + y**2 <= 1  # True si le point est dans le cercle

pi_estime = 4 * np.sum(dans_cercle) / N

print("Pi estimé :", pi_estime)
print("Pi réel   :", np.pi)