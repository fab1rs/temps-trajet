"""Génère typiques.json : temps typique (historique du trafic) par sens, jour et créneau.

TomTom estime un départ futur à partir de l'historique du trafic, ce qui donne le temps
typique sans attendre d'avoir des mesures.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from trajet import JOURS, PARIS, SENS, appeler_tomtom, points

SORTIE = Path(__file__).parent / "typiques.json"


def calculer(sens, cle):
    origine, destination = points(sens)
    demain = datetime.now(PARIS).date() + timedelta(days=1)
    typiques, resume = {}, None
    for decalage in range(7):
        date = demain + timedelta(days=decalage)
        if date.weekday() > 5:  # pas le dimanche
            continue
        jour = JOURS[date.weekday()]
        typiques[jour] = {}
        for creneau in SENS[sens]:
            heure, minute = map(int, creneau.split(":"))
            depart = datetime(date.year, date.month, date.day, heure, minute, tzinfo=PARIS)
            resume = appeler_tomtom(origine, destination, cle, depart.isoformat(timespec="seconds"))
            typiques[jour][creneau] = round(resume["historicTrafficTravelTimeInSeconds"] / 60, 1)
        print(sens, jour, typiques[jour])
    return {
        "distance_km": round(resume["lengthInMeters"] / 1000, 1),
        "sans_trafic_min": round(resume["noTrafficTravelTimeInSeconds"] / 60, 1),
        "typiques": {j: typiques[j] for j in JOURS if j in typiques},
    }


def main():
    cle = os.environ["TOMTOM_API_KEY"]
    donnees = {"genere_le": datetime.now(PARIS).date().isoformat()}
    for sens in SENS:
        donnees[sens] = calculer(sens, cle)
    SORTIE.write_text(json.dumps(donnees, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
