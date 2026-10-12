# DataWizflow AI

Plateforme locale pour interroger une base ou un fichier en langage naturel, exécuter du SQL en lecture seule, visualiser le résultat et exporter.

Le modèle tourne via [Ollama](https://ollama.com) sur votre machine. Les mots de passe de connexion sont chiffrés. Le code de graphique généré s'exécute dans un processus séparé, avec une liste d'imports autorisés.

## Démarrage

Prérequis : Python 3.11 et Ollama.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy config\.env-template .env
ollama pull mistral
python scripts/generate_demo_db.py
python -m streamlit run app.py
```

Ouvrez l'URL affichée par Streamlit, en général `http://localhost:8501`.

La voix demande Whisper et ffmpeg. Sans ces deux outils, le reste de l'application fonctionne.

```powershell
winget install Gyan.FFmpeg
pip install openai-whisper
```

Le premier clic sur Transcrire télécharge le modèle indiqué par `WHISPER_MODEL` (par défaut `small`). Le texte apparaît dans la zone de question : relisez-le avant de générer le SQL.

## Parcours

1. **Connexion et sources** : profil SQLite, PostgreSQL, MySQL ou MSSQL, test de connexion, schéma, ou dépôt d'un CSV, Excel, Parquet ou JSON.
2. **NL2SQL** : question en français ou en anglais, SQL éditable, vérification, exécution, export CSV / Excel / Parquet, historique et vues.
3. **DataViz** : graphique Matplotlib ou Plotly à partir du dernier résultat, d'un fichier chargé, ou d'un nouvel upload.
4. **Assistant** : conseils, explication du dernier résultat, squelette de notebook.
5. **Configuration** : URL Ollama, modèle, température, délai, librairie par défaut, thème, diagnostics, journaux.

Le sélecteur FR / EN est dans la barre latérale de chaque page. Il change les textes de l'interface et la langue demandée au modèle.

## Sécurité

- Seuls `SELECT` et `WITH` sont exécutés. `DROP`, `DELETE`, `UPDATE`, `INSERT` et les requêtes multiples sont refusés.
- Un `LIMIT` est ajouté s'il manque. L'exécution SQL est plafonnée à 30 secondes.
- Les appels Ollama sont espacés d'au moins une seconde.
- Les mots de passe de `config/connections.yaml` sont stockés avec Fernet. La clé est `FERNET_KEY` ou `config/.fernet_key` (non versionné).
- Le code Python de DataViz ne peut importer que pandas, numpy, matplotlib, plotly et scipy.

## Démo

`scripts/generate_demo_db.py` crée `db/demo.db` avec les tables `regions`, `products`, `dates` et `sales` (500 ventes en 2024).

Un petit fichier d'exemple est aussi dans `examples/ventes_exemple.csv`.

## Tests

```powershell
pytest -q
```

## Docker

Ollama peut rester sur la machine hôte. Compose pointe l'application vers `http://host.docker.internal:11434`.

```powershell
docker compose up --build
```

Pour lancer aussi un conteneur Ollama :

```powershell
docker compose --profile with-ollama up --build
```

## Ce qui reste optionnel

Le cahier des charges marque comme bonus la lecture vocale des résultats, les alertes, l'export PDF de rapport et l'intégration Git. Ces éléments ne font pas partie de cette version.
