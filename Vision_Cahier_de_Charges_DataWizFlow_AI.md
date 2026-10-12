# 📊 DataWizard AI (renommé : DataWizflow AI)
## Vision Produit + Cahier des Charges Détaillé

---

## 🎯 Résumé Exécutif

**DataWizard AI** est une **plateforme intelligente d'interrogation et visualisation de données**, basée sur :
- Un **LLM local (Ollama)** pour comprendre le langage naturel.
- Une **interface intuitive (Streamlit)** accessible même aux non-techniciens.
- Un **support multi-sources** (bases SQL, fichiers CSV/Excel/Parquet).
- Un **support multilingue complet** (français & anglais).
- Une **approche vocale** pour poser des questions à l'app par la voix.

**Objectif final** : permettre à un analyste, scientifique des données ou DSI de :
- Poser des questions en langage naturel sur n'importe quelle donnée.
- Obtenir des visualisations instantanées sans coder.
- Télécharger les résultats dans plusieurs formats.
- Comprendre comment ça marche (aspect pédagogique fort).

---

## 📋 Table des matières

1. [Vision & Positionnement](#vision--positionnement)
2. [Objectifs Pédagogiques](#objectifs-pédagogiques)
3. [Personas & Cas d'Usage](#personas--cas-dusage)
4. [Fonctionnalités Détaillées](#fonctionnalités-détaillées)
5. [Architecture Technique](#architecture-technique)
6. [Stack Technologique](#stack-technologique)
7. [Plan de Développement](#plan-de-développement)
8. [Livrables Attendus](#livrables-attendus)
9. [Critères de Succès](#critères-de-succès)

---

## Vision & Positionnement

### Problématique

Aujourd'hui, l'analyse de données reste **verrouillée aux techniciens** :
- Les analystes doivent écrire des requêtes SQL.
- Les dataviz demandent de coder (Python, BI tools complexes).
- La barrière d'entrée est très haute pour des questions ad‑hoc.

### Solution

Une **plateforme unifiée** qui utilise :
- **LLM local** (indépendance, pas d'API tierce, data governance).
- **Speech-to-Text** (accessibilité totale).
- **Génération de code** (SQL et Python) depuis le langage naturel.
- **Support multi-langues & multi-formats** (flexibilité maximale).

### Positionnement

| Aspect | Position |
|--------|----------|
| **Cible** | Data analysts, data scientists, DSI, formateurs |
| **Différenciation** | Multilingue + voix + multi-sources + local (pas d'API tierce) |
| **Complexité** | Facile pour l'utilisateur, riche techniquement en backend |
| **Coût** | Gratuit (open-source), peut se déployer on-premise |

---

## Objectifs Pédagogiques

Ce projet **couvre les domaines suivants** et permet d'apprendre :

### Data Engineering
- Connexion à différents moteurs de bases (PostgreSQL, MySQL, SQLite, MSSQL).
- Conception & manipulation de schémas SQL via SQLAlchemy.
- Import/export multi-formats (CSV, Excel, Parquet, JSON).
- Gestion d'erreurs et transactions.

### Data Analysis & SQL
- Génération sécurisée de requêtes SQL via LLM.
- Validation et optimisation de requêtes.
- Prompt engineering pour le contexte SQL.
- Gestion des résultats et des métadonnées.

### Data Visualization
- Approche "requête en langage naturel → code de graphique".
- Choix entre visualisations statiques (Matplotlib) et interactives (Plotly).
- Principes de dataviz efficace et lisibilité.
- Export multi-formats (PNG, HTML, SVG).

### Data Science & Machine Learning
- Assistant qui recommande des modèles ML basés sur les données.
- Suggestions de features engineering.
- Interprétation des résultats pour les décideurs.
- Pipelines de données basiques.

### Large Language Models & Prompt Engineering
- Comment les LLM comprennent et transforment le langage naturel en code.
- Conception de prompts structurés et robustes.
- Gestion des erreurs du LLM (hallucinations, SQL incorrect).
- Fine-tuning conceptuel (amélioration des prompts).

### ML Ops & Software Engineering
- Structure en packages Python professionnel.
- Gestion de configuration (.env, profiles).
- Logging et monitoring.
- Sécurité (pas d'exécution arbitraire de code).
- Containerisation (Docker).
- Documentation et README structurés.

### NLP & Speech-to-Text
- Intégration de Whisper pour transcrire l'audio.
- Gestion multilingue (français / anglais).
- Correction et édition de transcriptions.

### Intégration Frontend-Backend
- Streamlit : création d'interfaces data-centriques.
- Gestion d'état dans Streamlit (session_state).
- Caching et optimisation des appels.
- UX/UI data-friendly.

---

## Personas & Cas d'Usage

### Persona 1 : L'Analyste Métier (Non-Technicien)

**Profil** : Responsable commercial, RH, ou opérations.  
**Compétence technique** : Excel, SQL basique, pas de Python.  
**Besoin** :
- "Quel est le CA par région ce mois-ci ?"
- "Combien de contrats expirés par mois ?"
- "Un graphique des embauches par trimestre ?"

**Cas d'usage** :
1. Se connecte à la plateforme.
2. Dicte sa question en français (vocal).
3. Relit et valide la transcription.
4. Reçoit les résultats + visualisation.
5. Télécharge en Excel pour sa présentation.

### Persona 2 : Le Data Analyst

**Profil** : SQL moyen, Python basique, 5 ans d'expérience.  
**Besoin** :
- Accélérer les analyses ad-hoc.
- Prototyper rapidement des dataviz.
- Comprendre comment le LLM transforme la requête en SQL.

**Cas d'usage** :
1. Charge un fichier Parquet (source directe).
2. Tape en anglais : "Correlation matrix of numerical columns, heatmap".
3. Valide le code généré et le modifie légèrement.
4. Exporte en PNG pour un rapport.

### Persona 3 : Le Data Scientist / ML Engineer

**Profil** : Expert Python/SQL/ML, orientation modélisation.  
**Besoin** :
- Prototyper des pipelines d'extraction/transformation.
- Utiliser l'app comme un lab pour l'ingénierie des features.
- Bénéficier de suggestions du LLM sur les modèles à tester.

**Cas d'usage** :
1. Importe un CSV de données brutes.
2. Pose une question mixte : "Crée des features statistiques par groupe et visualise avec PCA".
3. Récupère le code généré → l'adapte pour son pipeline.
4. Exporte en CSV pour un notebook Jupyter.

### Persona 4 : Le Formateur / Chercheur

**Profil** : Universitaire ou formateur en data science.  
**Besoin** :
- Outil pédagogique pour expliquer NL2SQL, LLM, dataviz.
- Cas d'usage réalistes pour les étudiants.
- Démonstration de concepts (prompt engineering, multi-langues, etc.).

**Cas d'usage** :
1. Crée un schéma d'exemple (ventes, employés, etc.).
2. Utilise l'app en cours pour montrer : "Voyez, on dicte en français, et ça génère du SQL !".
3. Montre les limites du LLM → comment l'améliorer avec des prompts meilleurs.
4. Demande aux étudiants de tester avec des questions de plus en plus complexes.

---

## Fonctionnalités Détaillées

### 1. Onglet "Connexion & Sources de Données"

**Objectif** : Permettre à l'utilisateur de choisir sa source de données (base SQL ou fichiers).

#### 1.1 Gestion des Profils de Connexion à la Base

- **Sélection du type de base** : SQLite, PostgreSQL, MySQL, MSSQL, Oracle, etc.
- **Formulaire adapté au type** :
  - SQLite : chemin local du fichier `.db`.
  - PostgreSQL/MySQL/MSSQL : host, port, user, password, database.
- **Test de connexion** : bouton "Vérifier la connexion" → affiche ✓ ou ✗ + erreur.
- **Sauvegarde de profils** :
  - Stockage dans un fichier `connections.yaml` (encrypted password si possible).
  - Permet de basculer rapidement entre bases sans resaisir les infos.
  - Option : sauvegarde locale dans SQLite interne (app.db).
- **Gestion sécurisée** :
  - Les mots de passe ne sont jamais affichés en clair.
  - Suggestion : utiliser `cryptography.fernet` pour chiffrer les credentials.

#### 1.2 Upload de Fichiers Tabulaires

- **Types acceptés** :
  - `.csv` → pandas.read_csv().
  - `.xlsx` / `.xls` → pandas.read_excel() avec openpyxl.
  - `.parquet` → pandas.read_parquet().
  - `.json` → pandas.read_json() (format tabulaire simple).
- **Multi-upload optionnel** : charger plusieurs fichiers à la fois.
- **Aperçu immédiat** :
  - Affiche les 5 premières lignes.
  - Détection des types de colonnes (int, float, string, datetime).
  - Stats basiques (nulls, cardinalité).
  - Taille du fichier.
- **Sauvegarde temporaire** :
  - Fichiers uploadés stockés en mémoire (session Streamlit) ou en dossier `/uploads`.
  - Nettoyage automatique à la fin de la session.

#### 1.3 Schéma Détecté

- **Pour la base SQL** :
  - Détection automatique via SQLAlchemy : tables, colonnes, types, PK, FK.
  - Génération d'une **description structurée du schéma** :
    ```
    TABLE: sales
    - id (INTEGER, PRIMARY KEY)
    - region (VARCHAR, NOT NULL)
    - amount (FLOAT)
    - date (DATE)
    - product_id (INTEGER, FOREIGN KEY → products.id)
    
    TABLE: products
    - id (INTEGER, PRIMARY KEY)
    - name (VARCHAR)
    - category (VARCHAR)
    ```
  - Affichage lisible + bouton "Copier schéma" (pour le pasting dans les prompts).

- **Pour un fichier tabulaire** :
  - Colonnes + types détectés par pandas.
  - Stats par colonne (min, max, mean, median, std pour numériques).
  - Exemples de valeurs.

#### 1.4 Choix de Langue

- **Switch global** : FR / EN.
- Affecte :
  - Tous les textes de l'interface.
  - Les placeholders et exemples de requêtes.
  - Les messages d'erreur.
  - Les prompts vers le LLM (Ollama reçoit une instruction "répondre en français" ou "en anglais").

### 2. Onglet "NL2SQL" – Interroger les Données

**Objectif** : Transformer une question en langage naturel (texte ou voix) → requête SQL → exécution → résultats.

#### 2.1 Zone de Requête (Texte)

- **Textarea** pour saisir la question en français ou anglais.
- **Exemples dynamiques** affichés selon la langue et la source active :
  - FR + Base ventes : "Quels sont les meilleures ventes par région en 2024 ?"
  - EN + Base ventes : "Show me the top 10 products by revenue"
- **Placeholder inspirant**.

#### 2.2 Mode Vocal (Speech-to-Text)

- **Bouton "Enregistrer une question"** :
  - Affiche un widget d'enregistrement (via `streamlit_webrtc` ou simple file upload).
  - L'utilisateur appuie, enregistre sa voix, puis relâche.
  - Format de sortie : fichier `.wav` ou `.m4a`.

- **Transcription (Whisper)** :
  - Import du modèle Whisper (ex. `openai/whisper-small`).
  - Transcription du fichier audio → texte en français ou anglais.
  - Apparition du texte transcrit dans une **zone éditable**.
  
- **Zone d'édition** :
  - L'utilisateur relit la transcription et peut corriger les erreurs.
  - Exemple : "Quels son les meilleures ventes" → correction en "Quels sont les meilleures ventes".
  
- **Envoi vers LLM** :
  - Le texte (original ou édité) est envoyé au LLM pour générer le SQL.

#### 2.3 Génération SQL via Ollama

**Prompt structuré** :
```
Tu es un expert SQL. Convertis la question suivante en SQL.

SCHÉMA DE LA BASE :
{schema_description}

RÈGLES :
- Utilise UNIQUEMENT les tables et colonnes décrites ci-dessus.
- Dialecte SQL : {dialect} (ex. PostgreSQL, SQLite, MySQL)
- Pas de UPDATE, DELETE, DROP – LECTURE SEULE.
- Si la question est ambiguë, préfère les agrégations sur la colonne clé.
- Ajoute des commentaires pour clarifier les jointures.

QUESTION EN {language} :
{user_question}

RÉPONSE (SQL UNIQUEMENT, pas d'explications) :
```

**Appel au LLM** :
- Via `ollama` Python client (ex. `ollama.chat(model='mistral', ...)`).
- Parsing de la réponse pour extraire le SQL.

**Affichage du SQL généré** :
- Zone code avec syntax highlighting.
- Boutons : "Copier", "Éditer", "Exécuter".

#### 2.4 Révision & Édition avant Exécution

- **Mode "Expert"** : l'utilisateur peut modifier le SQL avant exécution.
- **Bouton "Vérifier la syntaxe"** (optionnel) :
  - Parsing léger du SQL pour détecter les erreurs évidentes.
  - Connexion test pour vérifier que la requête est valide (dry-run si possible).
- **Validations automatiques** :
  - Refuser les requêtes contenant DROP, DELETE, TRUNCATE.
  - Limiter la requête à 1000 lignes par défaut (sécurité).

#### 2.5 Exécution & Résultats

**Exécution** :
- Via SQLAlchemy : `connection.execute(text(sql_query))`.
- Gestion des erreurs :
  - Si erreur SQL → affiche le message d'erreur proprement.
  - Propose de corriger la requête ou d'essayer une autre approche.
- Timeout : limiter l'exécution à 30 secondes (éviter les requêtes trop lourdes).

**Affichage des résultats** :
- **Tableau pagé** :
  - Affiche les 50 premières lignes par défaut.
  - Pagination : "Page 1/5", avec boutons Next/Previous.
  - Recherche/filtre dans les résultats.
  - Option : tri par colonne.
- **Statistiques** :
  - Nombre total de lignes.
  - Schéma du résultat (colonnes + types).
- **Métadonnées de la requête** :
  - Temps d'exécution (en ms).
  - SQL exécuté (zone lisible).

#### 2.6 Téléchargement des Résultats

- **Bouton "Télécharger en CSV"** :
  - Export complet du résultat (toutes les lignes) en `.csv`.
  - Encoding UTF-8 (pour supporter accents français).
  
- **Bouton "Télécharger en Excel"** :
  - Export en `.xlsx` via `openpyxl` avec formatage basique (en-têtes gras, colonnes auto-width).

- **Bouton "Télécharger en Parquet"** :
  - Export en `.parquet` (format efficace, conserve les types).

#### 2.7 Sauvegarde comme Vues

- **Zone "Sauvegarder cette requête"** :
  - Champ "Nom de la vue" : ex. "CA par région 2024".
  - Champ "Description" (optionnel).
  - Bouton "Sauvegarder".
  
- **Stockage** :
  - Sauvegarde dans une table SQLite interne (`app.db`) :
    ```sql
    CREATE TABLE saved_views (
      id INTEGER PRIMARY KEY,
      name VARCHAR,
      description TEXT,
      sql_query TEXT,
      source_database VARCHAR,
      language VARCHAR (FR/EN),
      created_at TIMESTAMP,
      user_ip VARCHAR
    );
    ```
  - Ou dans un fichier YAML local (plus simple).

- **Réutilisation** :
  - Onglet "Mes vues" affiche la liste des vues sauvegardées.
  - Clic sur une vue → rechargement du SQL + exécution optionnelle.

#### 2.8 Historique des Requêtes

- **Log automatique** de chaque requête (NL, SQL généré, résultats count, timestamp).
- **Affichage** dans une section "Historique" :
  - Tableau avec colonnes : Question NL | SQL | Résultat (# lignes) | Date.
  - Possibilité de relancer une requête précédente en un clic.
- **Stockage** : table `queries_history` dans la base interne.

---

### 3. Onglet "DataViz" – Visualiser les Données

**Objectif** : Charger un CSV / fichier tabulaire / résultats NL2SQL → demander une visualisation en langage naturel → générer du code Matplotlib/Plotly → affichage interactif.

#### 3.1 Sélection de la Source

- **3 options** :
  1. Upload d'un CSV / Excel / Parquet / JSON.
  2. Sélection d'un fichier déjà uploadé dans la session.
  3. Sélection des résultats d'une requête NL2SQL précédente.

#### 3.2 Aperçu du Dataset

- **Affichage des 10 premières lignes**.
- **Infos structurelles** :
  - Nombre de lignes et colonnes.
  - Types de colonnes (int, float, string, datetime, boolean).
  - Colonnes numériques, catégorielles, dates.
  - Comptage de valeurs null.

#### 3.3 Requête de Visualisation (Texte ou Vocal)

- **Textarea ou zone d'enregistrement vocal** (même pattern que NL2SQL).
- **Exemples dynamiques** selon les colonnes détectées :
  - "Histogramme des salaires"
  - "Scatter plot salary vs years_experience"
  - "Box plot de la variable revenue par category"
  - "Time series du nombre de ventes par jour"

#### 3.4 Choix du Type de Graphique

- **Options** :
  - ☐ Statique (Matplotlib).
  - ☐ Interactif (Plotly).
  
- **Impact** :
  - Matplotlib → PNG/PDF, rapide, simple.
  - Plotly → HTML interactif (zoom, hover, export), moderne.

#### 3.5 Génération de Code via Ollama

**Prompt structuré** :
```
Tu es un expert en dataviz Python avec Matplotlib et Plotly.

DONNÉES DISPONIBLES :
Colonnes : {column_list}
Types : {column_types}
Exemples : {sample_data}

TÂCHE :
Génère du code Python {library} pour créer la visualisation suivante :
"{user_request}"

CONTRAINTES :
- Importe UNIQUEMENT : pandas, matplotlib.pyplot, plotly.express, numpy (si nécessaire).
- Ne fais PAS de calculs lourds ou d'appels externes.
- Code court et lisible.
- Gère les valeurs manquantes (dropna, fillna).
- Utilise des colors et styles professionnels.

CODE (UNIQUEMENT LE CODE, pas d'explications) :
```

**Appel au LLM** : même pattern que NL2SQL.

#### 3.6 Affichage du Code

- **Zone code** avec syntax highlighting (Python).
- **Boutons** : "Copier", "Éditer", "Exécuter".

#### 3.7 Exécution du Code (Sandbox Sécurisé)

- **Environnement restreint** :
  - Imports autorisés : `pandas`, `matplotlib`, `plotly`, `numpy`, `scipy.stats`.
  - Pas d'accès au disque, pas d'imports dynamiques.
  - Timeout : 10 secondes.
  
- **Implémentation** :
  - Utiliser `RestrictedPython` ou une approche sandboxée.
  - Ou exécuter via `exec()` avec un contexte contrôlé.
  
- **Gestion des erreurs** :
  - Erreur de code → affiche le traceback proprement.
  - Suggestion : "Vérifiez les noms de colonnes".

#### 3.8 Affichage du Graphique

- **Matplotlib** → affichage statique en PNG dans Streamlit.
- **Plotly** → affichage interactif avec zoom, hover tooltips, export bouton intégré.

#### 3.9 Téléchargement de la Visualisation

- **Pour Matplotlib** :
  - Bouton "Télécharger en PNG".
  - Bouton "Télécharger en PDF".
  
- **Pour Plotly** :
  - Bouton "Télécharger en HTML" (fichier complet, réouverture possible).
  - Bouton "Télécharger en PNG" (via Kaleido).

---

### 4. Onglet "Assistant Data / ML" (Bonus)

**Objectif** : Fournir des conseils et analyses générales basées sur le LLM.

#### 4.1 Conseils Data Science

- **Zone de chat** : l'utilisateur pose une question ouverte.
- **LLM génère des conseils** sur :
  - Modèles ML adaptés aux données.
  - Features à créer (feature engineering).
  - Anomalies à investiguer.
  - Interprétations des graphes/résultats.

#### 4.2 Génération de Notebooks

- **Bouton "Générer un skeleton de notebook"** :
  - Le LLM génère un outline en Markdown + code Python pour :
    - Préparation des données.
    - Exploration / EDA.
    - Features engineering.
    - Entraînement d'un modèle simple (ex. logistic regression, linear regression).
    - Évaluation et visualisation des résultats.
  - L'utilisateur peut copier/coller dans Jupyter.

#### 4.3 Explication de Résultats

- **Textarea** : "Explique-moi ce résultat" + contexte (CSV ou requête précédente).
- **LLM explique** simplement (niveau débutant ou expert selon le contexte).

---

### 5. Onglet "Configuration & Paramètres"

#### 5.1 Langue Globale

- **Switch FR / EN** → affecte toute l'interface et les prompts.

#### 5.2 Paramètres Ollama

- **URL Ollama** : par défaut `http://localhost:11434`, modifiable.
- **Modèle utilisé** : par défaut `mistral`, modifiable (liste des modèles disponibles téléchargés).
- **Paramètres de température** : `0.1` à `1.0`, par défaut `0.3` (pour stabilité SQL).
- **Timeout** : par défaut 60s.

#### 5.3 Profils de Connexion Base

- **Gestion des profils** : ajouter, supprimer, modifier.
- **Test rapide** pour chaque profil.

#### 5.4 Préférences DataViz

- **Libraire par défaut** : Matplotlib ou Plotly.
- **Thème** : light / dark.

#### 5.5 Logs & Diagnostics

- **Affichage des logs** (dernières 50 lignes).
- **Vérification de l'état** :
  - Ollama actif ? ✓/✗
  - Bases de données connectées ? ✓/✗
  - Whisper disponible ? ✓/✗

---

## Architecture Technique

### Diagramme d'Architecture Générale

```
┌─────────────────────────────────────────────────────────────────┐
│                         STREAMLIT FRONTEND                       │
│  ┌─────────────┬──────────────┬──────────────┬────────────────┐ │
│  │  Connexion  │  NL2SQL      │  DataViz     │  Assistant ML  │ │
│  │  & Sources  │              │              │                │ │
│  └─────────────┴──────────────┴──────────────┴────────────────┘ │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                ┌────────────────┼────────────────┐
                ▼                ▼                ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │  LLM Service │ │  DataViz     │ │ Speech-Text  │
        │  (Ollama)    │ │  Engine      │ │  (Whisper)   │
        └──────────────┘ └──────────────┘ └──────────────┘
                │                │                │
        ┌───────────────────────────────────────────────┐
        │            CORE SERVICES LAYER                │
        │  ┌────────────────────────────────────────┐  │
        │  │ • SQL Executor (SQLAlchemy)            │  │
        │  │ • File Loader (CSV, Excel, Parquet)   │  │
        │  │ • Prompt Generator                    │  │
        │  │ • Code Executor (Sandbox)             │  │
        │  │ • Config Manager                      │  │
        │  └────────────────────────────────────────┘  │
        └───────────────────────────────────────────────┘
                │                │                │
        ┌───────┴────────┬───────┴────────┬──────┴──────┐
        ▼                ▼                ▼             ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐ ┌─────────┐
    │   User     │  │   Base     │  │   Data    │  │  Cache  │
    │  Files    │  │ Connections│  │ Warehouse │  │  Layer  │
    └────────────┘  └────────────┘  └────────────┘ └─────────┘
```

### Composants Clés

#### 1. **Couche Frontend (Streamlit)**

- `app.py` : point d'entrée principal.
- `pages/` : modules pour chaque onglet.
  - `connection.py` : gestion des connexions.
  - `nl2sql.py` : interface NL2SQL.
  - `dataviz.py` : interface DataViz.
  - `assistant.py` : interface Assistant ML.
  - `config.py` : paramètres.

#### 2. **Couche Services**

- `services/ollama_client.py` :
  - Classe `OllamaService` avec méthodes :
    - `generate_sql(question, schema, dialect, language)`.
    - `generate_viz_code(request, columns, library)`.
    - `get_advice(prompt, context)`.

- `services/sql_executor.py` :
  - Classe `SQLExecutor` :
    - `connect(profile)`.
    - `get_schema()`.
    - `execute_query(sql, max_rows=1000)`.
    - `validate_query(sql)`.

- `services/speech_to_text.py` :
  - Classe `WhisperService` :
    - `transcribe(audio_file, language)`.

- `services/dataviz_engine.py` :
  - Classe `DataVizEngine` :
    - `execute_code(code, df, library)`.
    - `render_graph()`.

- `services/config_manager.py` :
  - Classe `ConfigManager` :
    - Gestion des profils de connexion (YAML/JSON).
    - Chiffrement des passwords.
    - Chargement de `.env`.

- `services/file_loader.py` :
  - Classe `FileLoader` :
    - `load_csv(filepath)`.
    - `load_excel(filepath)`.
    - `load_parquet(filepath)`.
    - `load_json(filepath)`.
    - Détection automatique du format.

#### 3. **Couche Utilitaires**

- `utils/prompts.py` :
  - Templates de prompts (NL2SQL, DataViz, Assistant).
  - Gestion de la langue (FR/EN).

- `utils/validators.py` :
  - Validation des requêtes SQL (pas de DROP, etc.).
  - Validation des inputs utilisateur.

- `utils/formatters.py` :
  - Formatage des résultats (tables, graphes).
  - Export CSV/Excel/Parquet.

- `utils/logger.py` :
  - Logging centralisé.

#### 4. **Couche Persistance**

- `db/internal.db` (SQLite) :
  - Tables : `saved_views`, `queries_history`, `connection_profiles`.
- `config/connections.yaml` : profils de connexion (encrypted).
- `config/.env` : variables d'environnement.

---

## Stack Technologique

### Détail du Stack

| Composant | Tech | Version | Raison |
|-----------|------|---------|--------|
| **Frontend** | Streamlit | 1.36+ | Simple, data-native, pas JS |
| **LLM Local** | Ollama | Latest | Local, pas d'API tierce, rapide |
| **BD Accès** | SQLAlchemy | 2.0+ | Support multi-DB unifié |
| **STT** | Whisper (openai) | Latest | Multilingue, local |
| **DataViz** | Matplotlib + Plotly | Latest | Static + interactive |
| **Upload Audio** | streamlit-webrtc | 0.47+ | Enregistrement in-browser |
| **Fichiers** | pandas, openpyxl, fastparquet | Latest | Support CSV/Excel/Parquet |
| **Config** | python-dotenv, PyYAML | Latest | Gestion config + secrets |
| **Sécurité** | cryptography | Latest | Encryption passwords |
| **Sandbox Code** | RestrictedPython | Latest | Exécution sécurisée |
| **Logs** | Python logging | Built-in | Monitoring |
| **Tests** | pytest | Latest | Tests unitaires |
| **Containerization** | Docker | Latest | Déploiement |

### Requirements.txt (Exemple complet)

```
# Frontend
streamlit==1.36.0
streamlit-webrtc==0.47.1

# LLM
ollama==0.1.0

# Speech-to-Text
openai-whisper==20231117

# Data Handling
pandas==2.1.0
openpyxl==3.11.0
fastparquet==2023.10.0

# Visualization
matplotlib==3.8.0
plotly==5.17.0

# Database
sqlalchemy==2.0.0
psycopg2-binary==2.9.0  # PostgreSQL driver
pymysql==1.1.0          # MySQL driver

# Config & Security
python-dotenv==1.0.0
pyyaml==6.0.0
cryptography==41.0.0

# Code Execution
RestrictedPython==6.1

# Utils
numpy==1.24.0
scipy==1.11.0
Pillow==10.0.0

# Development
pytest==7.4.0
black==23.11.0
flake8==6.1.0
```

---

## Plan de Développement

### Phase 1 : Fondations & Setup (Semaine 1 - Sprint)

**Durée** : 3-4 jours  
**Livrables** : Structure projet, base Streamlit, gestion des connexions.

#### Tâches

1. **Setup du projet** :
   - Créer structure de dossiers (app/, services/, utils/, config/, db/).
   - Initialiser `.gitignore`, `requirements.txt`, `.env-template`.
   - Créer `app.py` avec tabs de base.

2. **Gestion des connexions** :
   - Implémenter `ConfigManager` (YAML + chiffrement passwords).
   - Implémenter `SQLExecutor` basique (connexion SQLAlchemy).
   - Créer une page "Connexion & Sources" (UI Streamlit).

3. **Tests de base** :
   - Test unitaire : charger une config YAML.
   - Test unitaire : se connecter à SQLite de test.

4. **Créer la base de données de démo** :
   - Schéma simple : `sales`, `products`, `regions`, `dates`.
   - Données synthétiques (100-1000 lignes).

**Apprentissages clés** : SQLAlchemy, gestion de config, Streamlit basics.

---

### Phase 2 : NL2SQL (Semaine 2)

**Durée** : 4-5 jours  
**Livrables** : Génération SQL via Ollama, exécution, affichage résultats.

#### Tâches

1. **Intégration Ollama** :
   - Installer Ollama locally, télécharger modèle `mistral`.
   - Tester l'appel via Python (`ollama` client).
   - Implémenter `OllamaService.generate_sql()`.

2. **Prompt engineering** :
   - Créer le template de prompt NL2SQL (FR/EN).
   - Tester sur plusieurs exemples.
   - Ajouter des instructions strictes (pas de DROP, read-only).

3. **Interface NL2SQL** :
   - Créer page `nl2sql.py` dans Streamlit.
   - Zone de texte pour requête NL.
   - Bouton pour générer SQL.
   - Affichage du SQL généré (editable).
   - Bouton Exécuter.

4. **Affichage des résultats** :
   - Table paginée (streamlit.dataframe).
   - Bouton "Télécharger CSV".
   - Bouton "Télécharger Excel".

5. **Historique & Sauvegarde** :
   - Créer table `saved_views` en SQLite interne.
   - Bouton "Sauvegarder cette requête".
   - Affichage de l'historique.

6. **Tests** :
   - Test unitaire : `test_generate_sql_simple()`.
   - Test unitaire : `test_execute_query()`.
   - Test d'intégration : flux complet.

**Apprentissages clés** : Prompt engineering, NL2SQL patterns, gestion d'erreurs SQL, Streamlit session state.

---

### Phase 3 : Whisper & Entrée Vocale (Semaine 3)

**Durée** : 3-4 jours  
**Livrables** : Enregistrement audio, transcription, intégration NL2SQL.

#### Tâches

1. **Intégration Whisper** :
   - Installer `openai-whisper`.
   - Implémenter `WhisperService.transcribe()`.
   - Test local sur un fichier audio.

2. **Upload d'audio dans Streamlit** :
   - Utiliser `streamlit_webrtc` pour enregistrement in-browser.
   - Ou simple `st.file_uploader` pour upload.
   - Sauvegarde temporaire du fichier `.wav`.

3. **Transcription** :
   - Appel à Whisper pour convertir audio → texte.
   - Affichage du texte dans une zone éditable.
   - Support FR/EN (détection ou sélection utilisateur).

4. **Intégration au flux NL2SQL** :
   - Si utilisateur appuie "Enregistrer", on transcrit.
   - Le texte apparaît dans la zone de requête (éditable).
   - Reste du flux identique.

5. **Tests** :
   - Test unitaire : `test_transcribe_french()`, `test_transcribe_english()`.

**Apprentissages clés** : STT, Whisper, gestion audio, multilingue.

---

### Phase 4 : File Loader & Multi-Formats (Semaine 3)

**Durée** : 2-3 jours  
**Livrables** : Upload CSV, Excel, Parquet; affichage et métadonnées.

#### Tâches

1. **Implémentation FileLoader** :
   - Classe `FileLoader` avec méthodes pour chaque format.
   - Détection du format via extension.
   - Gestion des erreurs (fichier corrompu, etc.).

2. **UI pour upload** :
   - `st.file_uploader()` avec types multiples (CSV, XLSX, Parquet, JSON).
   - Affichage des 10 premières lignes.
   - Infos : # lignes, # colonnes, types, nulls.

3. **Intégration aux onglets** :
   - Fichier uploadé disponible dans NL2SQL comme source alternative.
   - Fichier disponible dans DataViz.

4. **Tests** :
   - Test load CSV, Excel, Parquet.

**Apprentissages clés** : pandas I/O, gestion de fichiers, détection de schémas.

---

### Phase 5 : DataViz (Semaine 4)

**Durée** : 5-6 jours  
**Livrables** : Génération de graphes via LLM, exécution, export.

#### Tâches

1. **Prompt pour DataViz** :
   - Template : génération de code Matplotlib/Plotly.
   - Inclure liste des colonnes, types, exemples.
   - Contraintes strictes (imports, sandbox).

2. **DataVizEngine** :
   - Classe pour exécuter du code Python dans un sandbox.
   - Utiliser `RestrictedPython` ou approche simple avec `exec()` limité.
   - Gérer les erreurs.

3. **Interface DataViz** :
   - Upload de CSV ou sélection fichier uploadé précédemment.
   - Requête en langage naturel (texte/vocal).
   - Choix : Matplotlib (statique) ou Plotly (interactif).
   - Affichage du code généré.

4. **Exécution & Affichage** :
   - Exécuter le code.
   - Afficher le graphique (via `st.pyplot()` ou `st.plotly_chart()`).

5. **Export** :
   - PNG pour Matplotlib.
   - HTML interactif pour Plotly.

6. **Tests** :
   - Test génération code simple.
   - Test exécution et affichage.

**Apprentissages clés** : Dataviz Python, génération de code, sandboxing, Plotly/Matplotlib.

---

### Phase 6 : Assistant Data & ML (Semaine 5)

**Durée** : 3-4 jours  
**Livrables** : Chat assistant, suggestions ML, skeleton notebooks.

#### Tâches

1. **Interface Chat** :
   - `st.chat_input()` et `st.chat_message()`.
   - Sauvegarde du contexte (session_state).

2. **Prompts pour Assistant** :
   - Template pour conseils data science.
   - Template pour explications de résultats.
   - Template pour skeleton notebook.

3. **Implémentation** :
   - Méthode `OllamaService.get_advice()`.
   - Affichage des réponses.
   - Bouton "Générer un notebook skeleton".

4. **Tests** :
   - Test intégration chat.

**Apprentissages clés** : LLM-based advisory, conversation, notebook generation.

---

### Phase 7 : Multilingue Complet (Semaine 5-6)

**Durée** : 2-3 jours  
**Livrables** : Support FR/EN global.

#### Tâches

1. **Système de traduction** :
   - Créer un fichier `translations.json` avec tous les textes (FR/EN).
   - Ou utiliser une librairie (ex. `i18n`).

2. **Intégration** :
   - Switch global FR/EN sur chaque page.
   - Tous les prompts adaptés à la langue.
   - Messages d'erreur traduits.

3. **Whisper** :
   - Paramètre de langue pour transcription.

4. **Tests** :
   - Test flux complet en français et anglais.

**Apprentissages clés** : Internationalization (i18n), multilingual LLM.

---

### Phase 8 : Configuration, Sécurité & Logs (Semaine 6)

**Durée** : 3-4 jours  
**Livrables** : Config centralisée, sécurité, logging.

#### Tâches

1. **ConfigManager avancé** :
   - Chiffrement passwords (Fernet).
   - Validation des entrées.
   - Gestion des secrets via `.env`.

2. **Logging** :
   - Logger centralisé avec rotating file handler.
   - Logs de toutes les requêtes.

3. **Page Configuration** :
   - Paramètres Ollama (URL, modèle, température).
   - Préférences DataViz.
   - Affichage des diagnostics (Ollama up?, DB connected?, Whisper ready?).

4. **Sécurité** :
   - Validation stricte des inputs.
   - Rate limiting sur les appels Ollama.
   - Sanitization de requêtes SQL.

5. **Tests** :
   - Test chiffrement passwords.
   - Test logging.

**Apprentissages clés** : Security best practices, logging, configuration management.

---

### Phase 9 : Tests Complets & Documentation (Semaine 7)

**Durée** : 3-4 jours  
**Livrables** : Suite de tests, README, guide utilisateur.

#### Tâches

1. **Tests unitaires** :
   - Chaque service : `test_*.py`.
   - Objectif : 80%+ de coverage.

2. **Tests d'intégration** :
   - Flux complets : NL2SQL → CSV, DataViz → PNG, etc.

3. **Documentation** :
   - README.md (installation, usage, architecture).
   - GUIDE_UTILISATEUR.md (tutoriel pour chaque onglet).
   - API documentation (docstrings complètes).

4. **Exemples** :
   - Cas d'usage réalistes avec schémas de test.
   - Captures d'écran des interfaces.

**Apprentissages clés** : Testing, documentation, best practices.

---

### Phase 10 : Dockerization & Déploiement (Semaine 8)

**Durée** : 2-3 jours  
**Livrables** : Dockerfile, docker-compose, guide de déploiement.

#### Tâches

1. **Dockerfile** :
   - Image Python 3.11+.
   - Installation des dépendances.
   - Expose port 8501 (Streamlit).

2. **docker-compose.yml** :
   - Service Streamlit.
   - Service Ollama (optionnel, ou lien à instance existante).
   - Volumes pour config et uploads.

3. **Documentation de déploiement** :
   - Local (docker-compose up).
   - Cloud (Heroku, AWS, GCP, etc.).

4. **Optimisation** :
   - Caching des modèles Whisper/Ollama.
   - Performance des grandes requêtes.

**Apprentissages clés** : Docker, containerization, MLOps basics.

---

### Phase 11 : Améliorations & Bonus (Semaine 9+)

**Durée** : Optionnel  
**Livrables** : Fonctionnalités bonus.

#### Idées

- **TTS (Text-to-Speech)** : lire les résultats à haute voix.
- **Collaborative filtering** : recommander des requêtes fréquentes.
- **Performance monitoring** : dashboards de métriques (temps de réponse, erreurs).
- **Fine-tuning des prompts** : interface pour améliorer les templates.
- **Export de vues en tant que rapports PDF**.
- **Intégration Git** : sauvegarder les requêtes en GitHub.
- **Alertes** : notifications si résultats changent de manière significative.

---

## Livrables Attendus

### À la fin du projet (Phase 11)

1. **Code Exécutable**
   - Repo GitHub (public ou privé).
   - Code bien structuré, commenté, PEP8.
   - 80%+ test coverage.

2. **Documentation Complète**
   - README.md (installation, usage, architecture).
   - Guide utilisateur (étape par étape).
   - Docstrings API (toutes les fonctions).
   - Diagrammes d'architecture (Lucidchart/Miro/ASCII).

3. **Containerization**
   - Dockerfile.
   - docker-compose.yml.
   - Guide de déploiement.

4. **Ressources d'Apprentissage**
   - Carnet de bord du projet (phases + learnings).
   - Notes sur concepts (NL2SQL, LLM, DataViz, etc.).
   - Cas d'usage réalistes.
   - Tutoriels (vidéo ou article) pour chaque onglet.

5. **Données & Exemples**
   - Base de données de démo (schéma + données).
   - CSVs d'exemple (sales, HR, e-commerce).
   - Requêtes NL2SQL d'exemple.
   - Prompts de visualisation d'exemple.

6. **Configuration & Déploiement**
   - `.env-template`.
   - Exemple de `connections.yaml`.
   - Scripts de setup (setup.sh pour Linux/Mac).
   - Makefile avec targets courants (install, run, test, docker).

---

## Critères de Succès

### Critères Techniques

- ✅ Génération SQL fonctionnelle pour les 80% des requêtes standards.
- ✅ Génération de graphes fonctionnelle (Matplotlib + Plotly).
- ✅ Transcription vocale (FR/EN) fiable.
- ✅ Support de 3+ types de bases (SQLite, PostgreSQL, MySQL).
- ✅ Support de 4+ formats de fichiers (CSV, Excel, Parquet, JSON).
- ✅ Temps de réponse < 5s pour requêtes standard.
- ✅ Pas de fuite de mémoire après 100+ requêtes.
- ✅ Taux d'erreur < 5% sur les exécutions.

### Critères d'UX

- ✅ Interface intuitive (non-technicien peut l'utiliser sans aide).
- ✅ Messages d'erreur clairs et constructifs.
- ✅ Suggestions d'amélioration intégrées (ex. "Vos données ont X nulls, à investiguer ?").
- ✅ Design propre et cohérent (couleurs, espacements, typo).

### Critères de Sécurité

- ✅ Pas d'exécution de DROP/DELETE/UPDATE par le LLM.
- ✅ Passwords jamais en clair (chiffrement).
- ✅ Code généré exécuté en sandbox (pas d'accès disque).
- ✅ Rate limiting sur appels LLM.

### Critères de Documentation

- ✅ README complet (< 5 min pour démarrer).
- ✅ Chaque fonction documentée (docstring + exemple).
- ✅ Architecture claire et diagrammes.
- ✅ Guide utilisateur avec screenshots.
- ✅ Troubleshooting pour les problèmes courants.

### Critères Pédagogiques

- ✅ Tous les concepts clés expliqués (NL2SQL, LLM, DataViz, etc.).
- ✅ Cas d'usage réalistes et diversifiés.
- ✅ Ressources d'apprentissage complémentaires (articles, vidéos).
- ✅ Code facilement adaptable pour projets dérivés.

---

## Conclusion

Ce projet **DataWizard AI** est conçu pour être :

- **Ambitieux** : couvre tout le spectre data science + LLM + MLOps.
- **Pédagogique** : excellente formation à plusieurs technologies clés.
- **Pratique** : une vraie application qu'on peut utiliser au quotidien.
- **Présentable** : portfolio project de haute qualité.
- **Extensible** : structure permettant d'ajouter des fonctionnalités facilement.

En suivant ce cahier des charges et le plan de développement, tu auras à la fin **une plateforme data intelligente, multilingue, multi-source, et prête pour l'industrie**.

---

**Bon développement ! 🚀**
