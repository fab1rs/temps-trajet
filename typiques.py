"""Génère typiques.json : temps typique (historique du trafic) par jour de semaine et créneau.

TomTom estime un départ futur à partir de l'historique du trafic, ce qui donne le temps
typique sans attendre d'avoir des mesures.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from trajet import CRENEAUX, JOURS, PARIS, appeler_tomtom

SORTIE = Path(__file__).parent / "typiques.json"


def main():
    origine, destination, cle = (os.environ[v] for v in ("ORIGINE", "DESTINATION", "TOMTOM_API_KEY"))
    demain = datetime.now(PARIS).date() + timedelta(days=1)
    typiques, resume = {}, None
    for decalage in range(7):
        date = demain + timedelta(days=decalage)
        if date.weekday() > 5:  # pas le dimanche
            continue
        jour = JOURS[date.weekday()]
        typiques[jour] = {}
        for creneau in CRENEAUX:
            heure, minute = map(int, creneau.split(":"))
            depart = datetime(date.year, date.month, date.day, heure, minute, tzinfo=PARIS)
            resume = appeler_tomtom(origine, destination, cle, depart.isoformat(timespec="seconds"))
            typiques[jour][creneau] = round(resume["historicTrafficTravelTimeInSeconds"] / 60, 1)
        print(jour, typiques[jour])

    SORTIE.write_text(json.dumps({
        "genere_le": datetime.now(PARIS).date().isoformat(),
        "distance_km": round(resume["lengthInMeters"] / 1000, 1),
        "sans_trafic_min": round(resume["noTrafficTravelTimeInSeconds"] / 60, 1),
        "typiques": {j: typiques[j] for j in JOURS if j in typiques},
    }, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
