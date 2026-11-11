# Temps de trajet A → B

Mesure automatiquement, du lundi au samedi, le temps de trajet en voiture toutes les 10 minutes,
à l'aller (A → B, de 7h00 à 8h00) et au retour (B → A, de 18h00 à 19h00), heure de Paris, via l'API TomTom.

Chaque mesure enregistre, pour le même départ :
- **réel** : temps avec le trafic en temps réel ;
- **typique** : temps prévu d'après l'historique du trafic à cette heure.

Résultats bruts dans `mesures.csv`, synthèse dans `RAPPORT.md` (mis à jour après chaque session).

## Configuration

Secrets du dépôt (*Settings → Secrets and variables → Actions*) :

| Secret | Exemple |
|---|---|
| `TOMTOM_API_KEY` | clé gratuite sur developer.tomtom.com |
| `ORIGINE` | `48.8566,2.3522` (latitude,longitude) |
| `DESTINATION` | `48.8925,2.2369` |

Test : onglet *Actions → Mesure temps de trajet → Run workflow* (fait une mesure immédiate).

## Page web

`index.html` affiche les temps typiques et réels par heure de départ, avec un onglet par jour.
Les temps typiques (`typiques.json`) sont recalculés le 1er de chaque mois par `typiques.py`.
