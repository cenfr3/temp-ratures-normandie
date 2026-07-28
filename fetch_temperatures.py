#!/usr/bin/env python3
"""
Récupère la température actuelle des 60 stations de Normandie (Open-Meteo)
et écrit temperatures.csv au format attendu par la carte Flourish :
Station, Latitude, Longitude, Temperature, Date_Mise_A_Jour

Robustesse : un seul appel réseau pour les 60 points. En cas d'erreur
(réseau, réponse incomplète), le script N'ÉCRIT PAS le fichier : la carte
garde ainsi la dernière donnée valide au lieu d'être vidée. Aucune
dépendance externe (bibliothèque standard uniquement).
"""

import csv
import json
import sys
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

FICHIER_SORTIE = "temperatures.csv"
FUSEAU = "Europe/Paris"

# (nom, latitude, longitude)
STATIONS = [
    ("Caen (14)", 49.18, -0.44000006),
    ("Bayeux (14)", 49.28, -0.70000005),
    ("Lisieux (14)", 49.14, 0.21999979),
    ("Vire Normandie (14)", 48.84, -0.8800001),
    ("Deauville (14)", 49.36, 0.07999992),
    ("Falaise (14)", 48.88, -0.20000005),
    ("Honfleur (14)", 49.42, 0.23999977),
    ("Cabourg (14)", 49.28, -0.16000009),
    ("Ouistreham (14)", 49.32, -0.3800001),
    ("Isigny-sur-Mer (14)", 49.2, -0.8800001),
    ("Villers-Bocage (14)", 49.08, -0.50000024),
    ("Livarot (14)", 49.02, 0.15999985),
    ("Cherbourg-en-Cotentin (50)", 49.64, -1.6400001),
    ("Saint-Lô (50)", 49.12, -1.0600002),
    ("Avranches (50)", 48.68, -1.3600001),
    ("Granville (50)", 48.84, -1.6000004),
    ("Coutances (50)", 49.04, -1.44),
    ("Valognes (50)", 49.5, -1.46),
    ("Sartilly (50)", 48.62, -1.5100002),
    ("Carentan (50)", 49.3, -1.44),
    ("Barneville-Carteret (50)", 49.43, -1.8100004),
    ("Bricquebec (50)", 49.66, -1.46),
    ("Lessay (50)", 49.41, -1.7300005),
    ("Cap de la Hague (50)", 49.72, -1.9300003),
    ("Alençon (61)", 48.44, 0.099999905),
    ("Flers (61)", 48.74, -0.5600002),
    ("Argentan (61)", 48.74, 0.019999743),
    ("Mortagne-au-Perche (61)", 48.52, 0.53999996),
    ("Vimoutiers (61)", 48.92, 0.19999981),
    ("L'Aigle (61)", 48.760002, 0.6199999),
    ("Sées (61)", 48.64, -0.120000124),
    ("Domfront en Poiraie (61)", 48.68, -0.74000025),
    ("La Ferté-Macé (61)", 48.6, -0.4000001),
    ("Longny les Villages (61)", 48.4, 0.85999966),
    ("Tourouvre au Perche (61)", 48.5, 0.42000008),
    ("Bagnoles de l'Orne (61)", 48.52, -0.22000003),
    ("Rouen (76)", 49.38, 1.1799998),
    ("Le Havre (76)", 49.5, 0.099999905),
    ("Dieppe (76)", 49.92, 1.0799999),
    ("Fécamp (76)", 49.760002, 0.37999964),
    ("Yvetot (76)", 49.62, 0.75999975),
    ("Barentin (76)", 49.54, 0.96000004),
    ("Neufchâtel-en-Bray (76)", 49.72, 1.44),
    ("Yerville (76)", 49.66, 0.6199999),
    ("Bolbec (76)", 49.48, 0.48000002),
    ("Pavilly (76)", 49.44, 0.7399998),
    ("Le Tréport (76)", 50.06, 1.3799996),
    ("Envermeu (76)", 49.86, 1.44),
    ("Saint-Saëns (76)", 49.52, 1.0),
    ("Lillebonne (76)", 49.38, 0.33999968),
    ("Évreux (27)", 49.02, 1.1599998),
    ("Vernon (27)", 49.1, 1.48),
    ("Louviers (27)", 49.2, 1.1599998),
    ("Gisors (27)", 49.28, 1.7799997),
    ("Pont-Audemer (27)", 49.34, 0.52),
    ("Les Andelys (27)", 49.4, 1.1199999),
    ("Gaillon (27)", 49.34, 1.52),
    ("Conches-en-Ouche (27)", 48.96, 1.3199997),
    ("Brionne (27)", 49.38, 1.2199998),
    ("Le Neubourg (27)", 49.24, 1.0),
]


def virgule(x):
    """Format français : point décimal -> virgule (comme l'ancien CSV)."""
    return str(x).replace(".", ",")


def main():
    lats = ",".join(str(s[1]) for s in STATIONS)
    lons = ",".join(str(s[2]) for s in STATIONS)
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lats}&longitude={lons}"
        "&current=temperature_2m"
        f"&timezone={FUSEAU.replace('/', '%2F')}"
    )

    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            if r.status != 200:
                print(f"HTTP {r.status} : sortie sans écrire (donnée précédente conservée).")
                return 0
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"Erreur réseau : {e} — sortie sans écrire (donnée précédente conservée).")
        return 0

    lieux = data if isinstance(data, list) else [data]  # multi-points = tableau
    if len(lieux) != len(STATIONS):
        print(f"Réponse incomplète ({len(lieux)}/{len(STATIONS)}) — sortie sans écrire.")
        return 0

    horodatage = datetime.now(ZoneInfo(FUSEAU)).strftime("%d/%m/%Y %H:%M:%S")

    lignes = [["Station", "Latitude", "Longitude", "Temperature", "Date_Mise_A_Jour"]]
    for (nom, lat, lon), lieu in zip(STATIONS, lieux):
        temp = (lieu.get("current") or {}).get("temperature_2m")
        temp_txt = "" if temp is None else virgule(f"{round(float(temp), 1):.1f}")
        lignes.append([nom, virgule(lat), virgule(lon), temp_txt, horodatage])

    # Les champs lat/lon/temp contiennent une virgule décimale : csv les met
    # automatiquement entre guillemets, exactement comme le fichier d'origine.
    with open(FICHIER_SORTIE, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(lignes)

    print(f"OK : {len(STATIONS)} stations écrites à {horodatage}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
