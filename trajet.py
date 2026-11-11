"""Mesure le temps de trajet en voiture entre ORIGINE et DESTINATION via l'API TomTom.

Deux sens : l'aller (ORIGINE → DESTINATION, le matin) et le retour (DESTINATION → ORIGINE, le soir).
Chaque mesure enregistre deux valeurs comparables pour le même départ :
  - reel_min     : temps avec le trafic en temps réel (ce qui se passe vraiment)
  - typique_min  : temps prévu d'après l'historique du trafic à cette heure-là
"""
import argparse
import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
SENS = {
    "aller": ["07:00", "07:10", "07:20", "07:30", "07:40", "07:50", "08:00"],
    "retour": ["18:00", "18:10", "18:20", "18:30", "18:40", "18:50", "19:00"],
}
TOLERANCE = timedelta(minutes=5)  # au-delà, un créneau est considéré comme manqué
FICHIER = Path(__file__).parent / "mesures.csv"
COLONNES = ["date", "jour", "sens", "creneau", "heure_mesure", "reel_min", "typique_min",
            "sans_trafic_min", "retard_trafic_min", "distance_km"]
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def points(sens):
    """(départ, arrivée) pour un sens donné."""
    a, b = os.environ["ORIGINE"], os.environ["DESTINATION"]
    return (a, b) if sens == "aller" else (b, a)


def appeler_tomtom(origine, destination, cle, depart="now"):
    url = (f"https://api.tomtom.com/routing/1/calculateRoute/"
           f"{urllib.parse.quote(origine)}:{urllib.parse.quote(destination)}/json?"
           + urllib.parse.urlencode({
               "key": cle,
               "travelMode": "car",
               "routeType": "fastest",
               "traffic": "true",
               "departAt": depart,
               "computeTravelTimeFor": "all",
           }))
    with urllib.request.urlopen(url, timeout=30) as reponse:
        return json.load(reponse)["routes"][0]["summary"]


def mesurer(sens, creneau, appel=appeler_tomtom):
    origine, destination = points(sens)
    cle = os.environ["TOMTOM_API_KEY"]
    for essai in range(3):
        try:
            resume = appel(origine, destination, cle)
            break
        except Exception as erreur:
            print(f"  essai {essai + 1} échoué : {erreur}", file=sys.stderr)
            time.sleep(10)
    else:
        print(f"  {sens} {creneau} : aucune mesure", file=sys.stderr)
        return None

    maintenant = datetime.now(PARIS)
    ligne = {
        "date": maintenant.date().isoformat(),
        "jour": JOURS[maintenant.weekday()],
        "sens": sens,
        "creneau": creneau,
        "heure_mesure": maintenant.strftime("%H:%M:%S"),
        "reel_min": round(resume["travelTimeInSeconds"] / 60, 1),
        "typique_min": round(resume["historicTrafficTravelTimeInSeconds"] / 60, 1),
        "sans_trafic_min": round(resume["noTrafficTravelTimeInSeconds"] / 60, 1),
        "retard_trafic_min": round(resume.get("trafficDelayInSeconds", 0) / 60, 1),
        "distance_km": round(resume["lengthInMeters"] / 1000, 1),
    }
    nouveau = not FICHIER.exists()
    with FICHIER.open("a", newline="") as f:
        ecrivain = csv.DictWriter(f, fieldnames=COLONNES)
        if nouveau:
            ecrivain.writeheader()
        ecrivain.writerow(ligne)
    print(f"  {sens} {creneau} → réel {ligne['reel_min']} min | typique {ligne['typique_min']} min")
    return ligne


def session(sens, decalage_attendu):
    """Fait les mesures d'un sens sur sa plage horaire (heure de Paris), une toutes les 10 minutes."""
    maintenant = datetime.now(PARIS)
    decalage = maintenant.utcoffset() // timedelta(hours=1)
    if decalage != decalage_attendu:
        # Deux crons existent par sens (heure d'été / d'hiver) : seul celui qui correspond à la saison mesure.
        print(f"Paris est en UTC+{decalage}, ce déclenchement (UTC+{decalage_attendu}) est ignoré.")
        return

    for creneau in SENS[sens]:
        heure, minute = map(int, creneau.split(":"))
        cible = maintenant.replace(hour=heure, minute=minute, second=0, microsecond=0)
        attente = (cible - datetime.now(PARIS)).total_seconds()
        if attente < -TOLERANCE.total_seconds():
            print(f"  {sens} {creneau} : manqué (déclenchement GitHub en retard)")
            continue
        if attente > 0:
            time.sleep(attente)
        mesurer(sens, creneau)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sens", choices=SENS, required=True)
    groupe = parser.add_mutually_exclusive_group(required=True)
    groupe.add_argument("--session", type=int, metavar="DECALAGE_UTC",
                        help="mesures sur la plage du sens si Paris est bien en UTC+DECALAGE_UTC")
    groupe.add_argument("--maintenant", action="store_true", help="une seule mesure immédiate (test)")
    args = parser.parse_args()
    if args.maintenant:
        mesurer(args.sens, datetime.now(PARIS).strftime("%H:%M"))
    else:
        session(args.sens, args.session)
