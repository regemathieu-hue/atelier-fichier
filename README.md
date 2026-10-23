# atelier-fichier

Pages publiques « Assistant » et « Politique de confidentialité », multilingues et multi-applications, servies par GitHub Pages.

## URL à déclarer pour chaque application

Remplacer `<app>` par l'identifiant de l'application défini dans `apps.json` (ex. `atelier-fichier`).

| Page | URL |
| --- | --- |
| Assistant (langue du navigateur) | `https://regemathieu-hue.github.io/atelier-fichier/<app>/assistant.html` |
| Confidentialité (langue du navigateur) | `https://regemathieu-hue.github.io/atelier-fichier/<app>/privacy.html` |
| Choix de langue | `https://regemathieu-hue.github.io/atelier-fichier/<app>/index.html` |
| Une langue précise | `https://regemathieu-hue.github.io/atelier-fichier/<app>/<locale>/assistant.html` ou `.../privacy.html` |

Les pages `assistant.html` et `privacy.html` d'une application redirigent vers la langue du navigateur (repli : `en-US`) et listent toutes les langues pour les navigateurs sans JavaScript. Chaque page porte des liens `hreflang` vers ses traductions.

## Langues

Une par fichier dans `i18n/` : ar-SA, ca, cs, da, de-DE, el, en-AU, en-CA, en-GB, en-US, es-ES, es-MX, fi, fr-CA, fr-FR, he, hi, hr, hu, id, it, ja, ko, ms, nl-NL, no, pl, pt-BR, pt-PT, ro, ru, sk, sv, th, tr, uk, vi, zh-Hans, zh-Hant.

## Ajouter une application

1. Ajouter une entrée dans `apps.json` :
   ```json
   { "id": "mon-app", "name": "Mon App", "repo": "https://github.com/regemathieu-hue/mon-app" }
   ```
   `id` devient le dossier (et donc l'URL), `name` est injecté dans tous les textes, `repo` sert aux liens « code source » et « tickets ».
2. Lancer `python3 build.py`, puis commiter les fichiers générés.

## Modifier un texte ou une traduction

1. Éditer `i18n/<locale>.json` (mêmes clés dans toutes les langues ; les placeholders `{app}`, `{date}`, `{privacy_link}`, `{issues_link}` doivent être conservés). La date de mise à jour est dans `apps.json`.
2. Lancer `python3 build.py`. Le script refuse de générer si une clé ou un placeholder manque.
3. Commiter.

## Activer GitHub Pages

1. Sur GitHub, ouvrir **Settings → Pages**.
2. Dans **Build and deployment**, choisir **Source : Deploy from a branch**.
3. Sélectionner la branche `main` et le dossier `/ (root)`, puis **Save**.

## Arborescence

- `apps.json` : applications, URL de base, langue par défaut, date de mise à jour.
- `i18n/*.json` : chaînes traduites.
- `templates/` : gabarits HTML.
- `build.py` : générateur (Python 3, sans dépendance).
- `<app>/` : pages générées (ne pas éditer à la main).
- `assets/style.css` : feuille de style commune.
- `index.html` : liste des applications. `assistant.html`, `privacy.html`, `confidentialite.html` : redirections vers la première application.
