"""Génère RAPPORT.md : temps réels vs typiques, par jour de la semaine et par créneau."""
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean

from trajet import CRENEAUX, FICHIER, JOURS

SORTIE = Path(__file__).parent / "RAPPORT.md"


def ecart(reel, typique):
    d = reel - typique
    return f"{'+' if d >= 0 else ''}{d:.1f}"


def main():
    if not FICHIER.exists():
        return
    with FICHIER.open() as f:
        lignes = list(csv.DictReader(f))
    if not lignes:
        return

    groupes = defaultdict(list)
    for l in lignes:
        groupes[(l["jour"], l["creneau"])].append((float(l["reel_min"]), float(l["typique_min"])))

    jours = [j for j in JOURS if any(k[0] == j for k in groupes)]
    sortie = [
        "# Temps de trajet A → B",
        "",
        f"{len(lignes)} mesures du {lignes[0]['date']} au {lignes[-1]['date']}. "
        "Cellule : **réel moyen** / typique moyen (écart), en minutes.",
        "",
        "| Créneau | " + " | ".join(j.capitalize() for j in jours) + " |",
        "|---|" + "---|" * len(jours),
    ]
    for creneau in CRENEAUX:
        cellules = []
        for jour in jours:
            valeurs = groupes.get((jour, creneau))
            if not valeurs:
                cellules.append("–")
                continue
            r, t = mean(v[0] for v in valeurs), mean(v[1] for v in valeurs)
            cellules.append(f"**{r:.1f}** / {t:.1f} ({ecart(r, t)})")
        sortie.append(f"| {creneau} | " + " | ".join(cellules) + " |")

    sortie += ["", "## 10 dernières mesures", "",
               "| Date | Jour | Créneau | Réel | Typique | Écart |", "|---|---|---|---|---|---|"]
    for l in lignes[-10:][::-1]:
        r, t = float(l["reel_min"]), float(l["typique_min"])
        sortie.append(f"| {l['date']} | {l['jour']} | {l['creneau']} | {r} | {t} | {ecart(r, t)} |")

    SORTIE.write_text("\n".join(sortie) + "\n")


if __name__ == "__main__":
    main()
