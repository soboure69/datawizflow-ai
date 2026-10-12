# Guide utilisateur

## Préparer les données

Lancez l'application avec `python -m streamlit run app.py`.

Sur **Connexion et sources** :

- Le profil `demo` pointe vers `db/demo.db` s'il n'existe aucun profil.
- **Utiliser** fixe la source active pour NL2SQL et l'assistant.
- **Vérifier la connexion** confirme que la base répond.
- **Afficher le schéma** montre tables, types, clés primaires et clés étrangères. Le bloc de code a un bouton copier.
- Pour PostgreSQL, MySQL ou MSSQL, choisissez le type, remplissez hôte, port, utilisateur, mot de passe et base, puis enregistrez. Le mot de passe n'est plus relu en clair.
- Déposez un ou plusieurs fichiers CSV, Excel, Parquet ou JSON. L'aperçu montre 5 lignes, les types, les valeurs nulles et la cardinalité. Le fichier devient une petite base SQLite utilisable comme source.

La zone SQL de cette page n'accepte que des lectures.

## Poser une question

Ouvrez **NL2SQL**.

1. Choisissez la source dans la barre latérale, puis **Utiliser**.
2. Écrivez une question, chargez un exemple, ou déposez un fichier audio wav, mp3 ou m4a puis **Transcrire**. Relisez le texte : la transcription se corrige dans la zone de question.
3. **Générer le SQL**. Le texte est éditable.
4. **Vérifier la syntaxe** interroge la base sans afficher les lignes. **Valider et exécuter** lance la requête.
5. Filtrez, triez et changez de page dans le tableau. Le temps d'exécution et les types de colonnes sont affichés.
6. Téléchargez en CSV, Excel ou Parquet.
7. Donnez un nom et une description, puis sauvegardez la vue.

L'historique reste visible même sans résultat à l'écran. **Charger** remet la question et le SQL. **Charger et exécuter** relance la requête.

## Faire un graphique

Ouvrez **DataViz**.

- Source : nouveau fichier, fichier déjà chargé, ou dernier tableau NL2SQL.
- Choisissez Matplotlib (image) ou Plotly (graphique interactif).
- Décrivez le graphique, ou chargez un exemple proposé à partir des colonnes.
- Relisez le code Python, puis exécutez-le.
- Téléchargez PNG ou PDF pour Matplotlib, HTML pour Plotly. Le PNG Plotly n'apparaît que si le paquet `kaleido` est installé.

Si le code vise une colonne absente, le message d'erreur s'affiche sous le bouton. Corrigez les noms puis relancez.

## Demander un avis

Ouvrez **Assistant**.

Le contexte affiché reprend le schéma de la source active et un extrait du dernier résultat NL2SQL.

- Écrivez une question dans le chat.
- **Expliquer le dernier résultat** produit une lecture pour un décideur, puis une note technique.
- **Générer un squelette de notebook** produit du Markdown à coller dans Jupyter. Le code n'est pas exécuté par l'application.

## Réglages

Ouvrez **Configuration**.

- URL Ollama, modèle (liste des modèles téléchargés si Ollama répond), température, délai.
- Librairie de graphique par défaut et thème clair ou sombre. Le thème est pris en compte au prochain démarrage.
- Les diagnostics indiquent si Ollama, la base active et Whisper répondent.
- Les 50 dernières lignes de `logs/app.log` sont affichées.

## Langue

Le sélecteur **FR / EN** de la barre latérale change les libellés et la langue demandée au modèle. Une question peut être posée dans l'autre langue : le modèle suit la langue choisie dans le sélecteur pour ses consignes.

## En cas de blocage

- **Ollama ne répond pas** : vérifiez `ollama list` et l'URL dans Configuration. Le défaut est `http://localhost:11434`.
- **SQL refusé** : la requête doit commencer par `SELECT` ou `WITH`, sans point-virgule.
- **Voix indisponible** : installez ffmpeg (`winget install Gyan.FFmpeg`) et `pip install openai-whisper`, puis redémarrez l'application. Le premier clic sur Transcrire télécharge le modèle.
- **Driver PostgreSQL ou MySQL manquant** : ils sont dans `requirements.txt` (`psycopg2-binary`, `pymysql`). MSSQL demande en plus un driver ODBC installé sur la machine.
- **Graphique vide** : le code doit créer une variable `fig`.
