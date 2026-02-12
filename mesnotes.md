
## Oui, je vais expliquer le “pourquoi” à chaque étape

À partir de maintenant, pour chaque fichier/dossier/commande :
- **Pourquoi on le crée**
- **À quoi ça sert**
- **Ce que ça débloque plus tard** (Phase 2/3)

---

# Où mettre app.py

## Recommandation (simple pour débuter)
- **app.py à la racine du projet** ✅

### Pourquoi ?
- **Streamlit** lance très naturellement avec :
  - `streamlit run app.py`
- Le système de multipages Streamlit fonctionne “out of the box” si tu as :
  - app.py à la racine
  - un dossier pages/ à la racine

### Et le dossier `app/` alors ?
On l’a créé pour préparer une structure plus “propre” plus tard (quand on aura plus de code) :
- `app/` pourra contenir la logique applicative (ex: `app/main.py`, `app/ui/`, etc.)
- mais **pour apprendre + avancer vite**, racine = plus simple et moins de friction.

## Alternative (plus “architecture”)
- `app/main.py` + lancer `streamlit run app/main.py`

Ça marche, mais :
- ça ajoute une couche d’organisation tout de suite
- et Streamlit multipage est souvent plus simple avec pages/ au même niveau que le fichier lancé

Donc on part sur **app.py à la racine**.

---


## 1) .gitignore — pourquoi ?
Pour éviter de versionner :
- l’environnement Python (.venv/)
- les bases locales (db/)
- les fichiers uploadés (uploads/)
- les caches / secrets (`.env`, logs)

## 2) requirements.txt (Choix A minimal) — pourquoi ?
On installe **uniquement** ce qu’il faut pour Phase 1 :
- UI Streamlit
- gestion config YAML
- connexion DB via SQLAlchemy
- tests

## 3) .env-template — pourquoi ?
- garder une “liste des variables” attendues sans secrets
- permettre à n’importe qui de configurer l’app localement

---
## Notes (pédagogie)
- ``streamlit`` : UI
- ``pyyaml`` : lire/écrire une config YAML (Phase 1 / tâche 2)
- ``python-dotenv`` : charger des variables d’environnement depuis `.env`
- ``sqlalchemy`` : couche DB (SQLite au début)
- ``pandas`` : pratique pour afficher des tables et manipuler des données (sera utile partout)
- ``pytest`` : tests unitaires (Phase 1 / tâche 3)

----


## Phase 1 — Tâche 2 : Gestion des connexions (ConfigManager + SQLExecutor + UI)

On va construire ça en 3 briques. À chaque brique je t’explique **pourquoi** et tu fais l’action **toi-même** (copier/coller).

---

# 0) Pré-requis : créer ton `.env`

## Pourquoi ?
- `.env` contient **tes valeurs locales** (donc non versionnées).
- [config/.env-template](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/config/.env-template:0:0-0:0) reste le “contrat” versionné.

## Action (toi)
1) Crée un fichier **`.env`** à la racine (à côté de [app.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/app.py:0:0-0:0))
2) Copie/colle dedans :

```env
APP_ENV=dev
DATABASE_URL=sqlite:///db/demo.db
```

---

# 1) ConfigManager (YAML + “placeholders” secrets)

## Pourquoi ?
- Centraliser la config projet dans un fichier YAML lisible.
- Éviter de disperser les paramètres dans le code.
- Préparer la suite : plusieurs connexions, plusieurs sources, etc.

## Ce qu’on va créer
- `config/config.yaml` : configuration “non sensible”
- `services/config_manager.py` : lecture/écriture + fusion éventuelle avec `.env`

### Action (toi) : créer `config/config.yaml`
```yaml
app:
  name: DataWizflow AI
  default_language: FR

database:
  url: ${DATABASE_URL}
```

### Action (toi) : créer `services/config_manager.py`
Copie/colle :

```python
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


_ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


def _substitute_env_vars(value: str) -> str:
    def repl(match: re.Match[str]) -> str:
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))

    return _ENV_PATTERN.sub(repl, value)


def _walk_and_substitute(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _walk_and_substitute(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk_and_substitute(v) for v in obj]
    if isinstance(obj, str):
        return _substitute_env_vars(obj)
    return obj


@dataclass(frozen=True)
class AppConfig:
    raw: dict[str, Any]

    @property
    def database_url(self) -> str:
        db = self.raw.get("database", {})
        url = db.get("url")
        if not url or not isinstance(url, str):
            raise ValueError("Missing database.url in config")
        return url


class ConfigManager:
    def __init__(self, config_path: str = "config/config.yaml") -> None:
        self._path = Path(config_path)

    def load(self) -> AppConfig:
        if not self._path.exists():
            raise FileNotFoundError(f"Config file not found: {self._path}")

        data = yaml.safe_load(self._path.read_text(encoding="utf-8")) or {}
        data = _walk_and_substitute(data)
        return AppConfig(raw=data)
```

### Pourquoi `${DATABASE_URL}` ?
- Ça te permet de garder `config.yaml` générique,
- et de changer de DB juste via `.env` sans toucher le YAML.

---

# 2) SQLExecutor (SQLAlchemy)

## Pourquoi ?
- Une couche unique qui gère la connexion DB et l’exécution de requêtes.
- Ça évite de mettre du SQLAlchemy partout dans les pages Streamlit.
- Prépare le futur : Postgres/MySQL, pool, timeouts, read-only, etc.

## Action (toi) : créer `services/sql_executor.py`

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


@dataclass(frozen=True)
class QueryResult:
    columns: list[str]
    rows: list[tuple[Any, ...]]


class SQLExecutor:
    def __init__(self, database_url: str) -> None:
        self._engine: Engine = create_engine(database_url, future=True)

    @property
    def engine(self) -> Engine:
        return self._engine

    def test_connection(self) -> None:
        with self._engine.connect() as conn:
            conn.execute(text("SELECT 1"))

    def execute(self, sql: str, params: Optional[dict[str, Any]] = None) -> QueryResult:
        with self._engine.connect() as conn:
            result = conn.execute(text(sql), params or {})
            if result.returns_rows:
                rows = result.fetchall()
                columns = list(result.keys())
                return QueryResult(columns=columns, rows=[tuple(r) for r in rows])
            return QueryResult(columns=[], rows=[])
```

---

# 3) Page “Connexion & Sources” (UI Streamlit)

## Pourquoi ?
- Un écran dédié pour :
  - visualiser la DB configurée
  - tester la connexion
  - exécuter un SQL simple “sanity check”

## Action (toi) : créer `pages/1_Connexion_&_Sources.py`

```python
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from services.config_manager import ConfigManager
from services.sql_executor import SQLExecutor

load_dotenv()

st.title("Connexion & Sources")

cfg = ConfigManager().load()
st.write("Database URL:")
st.code(cfg.database_url)

executor = SQLExecutor(cfg.database_url)

col1, col2 = st.columns([1, 2])
with col1:
    if st.button("Tester la connexion"):
        try:
            executor.test_connection()
            st.success("Connexion OK")
        except Exception as e:
            st.error(str(e))

with col2:
    st.caption("Test simple : SELECT 1, ou création table de démo ensuite (Phase 1 / tâche 4).")

st.subheader("Exécuter une requête SQL (lecture)")
sql = st.text_area("SQL", value="SELECT 1 AS ok", height=120)

if st.button("Exécuter"):
    try:
        res = executor.execute(sql)
        if res.rows and res.columns:
            df = pd.DataFrame(res.rows, columns=res.columns)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Requête exécutée (aucun résultat à afficher).")
    except Exception as e:
        st.error(str(e))
```

---

# Étape suivante (toi) : test rapide

1) Installe `python-dotenv` est déjà dans requirements ✅  
2) Lance l’app, puis va sur la page **Connexion & Sources**
3) Clique :
- **Tester la connexion**
- puis **Exécuter** sur `SELECT 1 AS ok`

---

## Dis-moi quand c’est fait
Réponds avec :
- “OK connexion” si ça marche
- ou colle l’erreur exacte

Ensuite on enchaîne Phase 1 — **Tâche 3 : Tests de base (pytest)**, puis Tâche 4 : **base de données de démo** (tables `sales/products/regions/dates` + génération synthétique).

----

## Phase 1 — Tâche 3 : Tests de base (pytest)

Objectif : avoir **2 tests simples** qui te donnent confiance :
- **Test 1** : le YAML est bien chargé + substitution `${DATABASE_URL}` OK
- **Test 2** : on peut se connecter à **une SQLite de test** et faire `SELECT 1`

> Idée pédagogique : on teste **la logique**, pas l’UI Streamlit.

---

# 1) Créer l’arborescence de tests

## Pourquoi ?
- `tests/` isole les tests du code applicatif.
- pytest découvre automatiquement les fichiers `test_*.py`.

## Action (toi)
Vérifie que le dossier `tests/` existe (tu l’as créé au setup). Sinon crée-le.

Puis crée ces fichiers :

- `tests/test_config_manager.py`
- `tests/test_sql_executor.py`

---

# 2) Test 1 — ConfigManager

## Pourquoi ?
- C’est ton “contrat” : si la config casse, tout casse.
- On valide la substitution `${DATABASE_URL}` sans dépendre de `.env` (tests reproductibles).

## Contenu à coller : `tests/test_config_manager.py`
```python
import os
from pathlib import Path

from services.config_manager import ConfigManager


def test_load_config_substitutes_env_var(tmp_path: Path, monkeypatch) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_path = config_dir / "config.yaml"
    config_path.write_text(
        "database:\n"
        "  url: ${DATABASE_URL}\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("DATABASE_URL", "sqlite:///db/test.db")

    cfg = ConfigManager(config_path=str(config_path)).load()
    assert cfg.database_url == "sqlite:///db/test.db"
```

---

# 3) Test 2 — SQLExecutor (SQLite)

## Pourquoi ?
- On valide que SQLAlchemy est bien installé/configuré.
- On teste une vraie connexion DB, mais **sans toucher** ta DB réelle (`db/demo.db`).

## Contenu à coller : `tests/test_sql_executor.py`
```python
from services.sql_executor import SQLExecutor


def test_sql_executor_can_connect_and_select_one() -> None:
    executor = SQLExecutor("sqlite+pysqlite:///:memory:")
    executor.test_connection()

    res = executor.execute("SELECT 1 AS ok")
    assert res.columns == ["ok"]
    assert res.rows == [(1,)]
```

---

# 4) Lancer les tests

## Pourquoi ?
- C’est le “bouton rouge” qui confirme que Phase 1 est stable.

## Action (toi)
Dans ton venv :
```powershell
pytest -q
```

---

# Point important : tu as probablement une petite erreur à corriger
Dans les fichiers que tu as créés, je vois des `.` en fin de fichier (ex: `return AppConfig(raw=data).`).

Ça va provoquer un **SyntaxError** au moment des tests.

## Action (toi) : corriger ces fins de fichiers
Vérifie et supprime le `.` final dans :
- [config/config.yaml](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/config/config.yaml:0:0-0:0) (tu as `url: ${DATABASE_URL}.` → il faut enlever le point)
- [services/config_manager.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/services/config_manager.py:0:0-0:0) (dernier `return ...` finit par `.`)
- [services/sql_executor.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/services/sql_executor.py:0:0-0:0) (retour finit par `.`)
- [pages/1_Connexion_&_Sources.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/pages/1_Connexion_&_Sources.py:0:0-0:0) (dernier `st.error(...)` finit par `.`)

> Pourquoi c’est arrivé ? Très souvent c’est un copier/coller qui inclut un caractère final parasite.

---

## Dis-moi le résultat
Après correction + `pytest -q`, réponds avec :
- la sortie pytest (2 lignes suffisent)
- ou la première erreur si ça échoue

Ensuite on passe à **Phase 1 — Tâche 4 : créer la base de données de démo** (`sales/products/regions/dates` + données synthétiques).

---
Je vais diagnostiquer pourquoi `pytest` ne trouve pas le module [services](cci:9://file:///c:/Users/bello/Documents/datawizflow-ai/services:0:0-0:0) (c’est un problème de “Python import path” / packaging). Ensuite je te propose la correction la plus simple et pédagogique (ajouter `__init__.py` et/ou un `conftest.py` qui ajoute la racine du projet au `sys.path`). Je commence par vérifier la structure actuelle du dossier.



## Pourquoi tu as `ModuleNotFoundError: No module named 'services'`
Quand `pytest` lance les tests, il ne garantit pas que la **racine du projet** ([datawizflow-ai/](cci:9://file:///c:/Users/bello/Documents/datawizflow-ai:0:0-0:0)) est dans le `PYTHONPATH`.

Résultat :
- `from services.config_manager import ConfigManager` échoue
- parce que Python ne “voit” pas [services/](cci:9://file:///c:/Users/bello/Documents/datawizflow-ai/services:0:0-0:0) comme un module importable.

Il y a 2 choses classiques à faire (et on va les faire de façon simple et pédagogique) :

---

# Fix 1 (obligatoire) : déclarer [services/](cci:9://file:///c:/Users/bello/Documents/datawizflow-ai/services:0:0-0:0) comme package Python

## Pourquoi ?
Un dossier n’est considéré comme un “package” Python que s’il contient un fichier `__init__.py` (même vide).

## Action (toi)
Crée ces fichiers vides :

- `services/__init__.py`
- (optionnel mais recommandé pour la suite) `utils/__init__.py`

---

# Fix 2 (recommandé) : dire à pytest d’ajouter la racine projet au `sys.path`

## Pourquoi ?
Même avec `__init__.py`, Python doit **trouver** le package : il faut que le parent ([datawizflow-ai/](cci:9://file:///c:/Users/bello/Documents/datawizflow-ai:0:0-0:0)) soit dans le path d’import.

La manière la plus simple en projet “apprentissage” : un `tests/conftest.py` qui ajoute la racine du repo au `sys.path`.

## Action (toi)
Crée le fichier `tests/conftest.py` avec ce contenu :

```python
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
```

---

# Important : tu as encore des `.` en fin de ligne dans tes tests
Dans ce que tu as créé, je vois :

- `assert cfg.database_url == "sqlite:///db/test.db".`
- `assert res.rows == [(1,)].`

Ces `.` vont provoquer une **SyntaxError** dès que les imports marcheront.

## Action (toi)
Corrige dans :
- [tests/test_config_manager.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/tests/test_config_manager.py:0:0-0:0) : enlève le `.` final
- [tests/test_sql_executor.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/tests/test_sql_executor.py:0:0-0:0) : enlève le `.` final

---

# Relance
Ensuite relance :

```powershell
pytest -q
```

## Attendu
- 2 tests passent ✅

---

## Dis-moi le résultat
Copie/colle la sortie de `pytest -q`.

Ensuite on enchaîne Phase 1 — **Tâche 4 : Base de données de démo** (schéma `sales/products/regions/dates` + génération synthétique).

---

## Phase 1 — Tâche 4 : créer la base de données de démo (`sales`, `products`, `regions`, `dates`)

### Pourquoi on fait ça ?
- **Avoir des données stables** pour tester l’app (requêtes SQL, UI, perf) sans dépendre d’un fichier externe.
- **Apprendre** : création de schéma, relations, insertion de données, et requêtes de validation.
- Ça servira directement en Phase 2 (NL2SQL) : on aura un modèle de données “propre”.

---

# 1) Schéma cible (simple et pédagogique)

- **`regions`** : liste des régions (id, nom)
- **`products`** : produits (id, nom, catégorie, prix)
- **`dates`** : dimension temps (date, année, mois, trimestre…)
- **`sales`** : faits de vente (date, région, produit, quantités, montant)

Relations :
- `sales.region_id -> regions.region_id`
- `sales.product_id -> products.product_id`
- `sales.sale_date -> dates.date`

---

# 2) Action (toi) : créer un script de génération

Crée le fichier : **`scripts/generate_demo_db.py`**  
(oui, on crée `scripts/` : c’est un endroit dédié aux scripts utilitaires, séparé des services/app)

## Contenu à copier/coller
```python
from __future__ import annotations

import os
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path


def create_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    cur.execute("PRAGMA foreign_keys = ON;")

    cur.executescript(
        """
        DROP TABLE IF EXISTS sales;
        DROP TABLE IF EXISTS dates;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS regions;

        CREATE TABLE regions (
            region_id INTEGER PRIMARY KEY,
            region_name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            unit_price REAL NOT NULL
        );

        CREATE TABLE dates (
            date TEXT PRIMARY KEY,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            day INTEGER NOT NULL,
            quarter INTEGER NOT NULL
        );

        CREATE TABLE sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_date TEXT NOT NULL,
            region_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            revenue REAL NOT NULL,

            FOREIGN KEY (sale_date) REFERENCES dates(date),
            FOREIGN KEY (region_id) REFERENCES regions(region_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );

        CREATE INDEX idx_sales_date ON sales(sale_date);
        CREATE INDEX idx_sales_region ON sales(region_id);
        CREATE INDEX idx_sales_product ON sales(product_id);
        """
    )
    conn.commit()


def seed_dimensions(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    regions = ["North", "South", "East", "West"]
    cur.executemany(
        "INSERT INTO regions(region_id, region_name) VALUES (?, ?)",
        [(i + 1, name) for i, name in enumerate(regions)],
    )

    products = [
        (1, "Laptop Pro 14", "Tech", 1299.0),
        (2, "Laptop Air 13", "Tech", 999.0),
        (3, "Mouse Wireless", "Tech", 29.0),
        (4, "Keyboard Mechanical", "Tech", 89.0),
        (5, "Desk Basic", "Office", 199.0),
        (6, "Chair Comfort", "Office", 149.0),
        (7, "Notebook A5", "Office", 4.5),
        (8, "Pen Black", "Office", 1.2),
        (9, "Coffee Beans", "Food", 8.9),
        (10, "Tea Green", "Food", 3.5),
    ]
    cur.executemany(
        "INSERT INTO products(product_id, product_name, category, unit_price) VALUES (?, ?, ?, ?)",
        products,
    )

    start = date(2024, 1, 1)
    end = date(2024, 12, 31)
    d = start
    rows = []
    while d <= end:
        q = (d.month - 1) // 3 + 1
        rows.append((d.isoformat(), d.year, d.month, d.day, q))
        d += timedelta(days=1)

    cur.executemany(
        "INSERT INTO dates(date, year, month, day, quarter) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()


def seed_sales(conn: sqlite3.Connection, n_rows: int = 500, seed: int = 42) -> None:
    random.seed(seed)
    cur = conn.cursor()

    # Load dimensions for random choices
    region_ids = [r[0] for r in cur.execute("SELECT region_id FROM regions").fetchall()]
    product_rows = cur.execute("SELECT product_id, unit_price FROM products").fetchall()
    products = [(pid, float(price)) for pid, price in product_rows]
    date_rows = cur.execute("SELECT date FROM dates").fetchall()
    dates = [d[0] for d in date_rows]

    sales = []
    for _ in range(n_rows):
        sale_date = random.choice(dates)
        region_id = random.choice(region_ids)

        product_id, unit_price = random.choice(products)

        # Quantity biased: small items sell more than expensive items
        if unit_price > 500:
            quantity = random.randint(1, 3)
        elif unit_price > 100:
            quantity = random.randint(1, 6)
        else:
            quantity = random.randint(1, 25)

        # Small random "discount noise" included directly in revenue
        discount = random.choice([0.0, 0.0, 0.05, 0.10, 0.15])
        revenue = quantity * unit_price * (1 - discount)

        sales.append((sale_date, region_id, product_id, quantity, revenue))

    cur.executemany(
        """
        INSERT INTO sales(sale_date, region_id, product_id, quantity, revenue)
        VALUES (?, ?, ?, ?, ?)
        """,
        sales,
    )
    conn.commit()


def main() -> None:
    db_url = os.environ.get("DATABASE_URL", "sqlite:///db/demo.db")
    if not db_url.startswith("sqlite:///"):
        raise ValueError("For Phase 1 demo, DATABASE_URL must be sqlite:///...")

    db_path = db_url.replace("sqlite:///", "", 1)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        create_schema(conn)
        seed_dimensions(conn)
        seed_sales(conn, n_rows=500, seed=42)
        print(f"Demo DB created at: {db_path}")
        print("Rows:")
        cur = conn.cursor()
        for table in ["regions", "products", "dates", "sales"]:
            n = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"- {table}: {n}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
```

---

# 3) Action (toi) : exécuter le script

Dans ton venv (à la racine du projet) :

```powershell
python scripts/generate_demo_db.py
```

Attendu :
- création de `db/demo.db`
- logs avec le nombre de lignes (environ `sales: 500`)

---

# 4) Validation dans l’UI (Connexion & Sources)

Dans la page **Connexion & Sources**, teste ces requêtes :

## Requête 1 — vérifier les tables
```sql
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
```

## Requête 2 — top catégories par revenu
```sql
SELECT p.category, ROUND(SUM(s.revenue), 2) AS revenue_total
FROM sales s
JOIN products p ON p.product_id = s.product_id
GROUP BY p.category
ORDER BY revenue_total DESC;
```

## Requête 3 — revenu par région
```sql
SELECT r.region_name, ROUND(SUM(s.revenue), 2) AS revenue_total
FROM sales s
JOIN regions r ON r.region_id = s.region_id
GROUP BY r.region_name
ORDER BY revenue_total DESC;
```

---

## Dis-moi où tu en es
Réponds avec :
- la sortie du script `generate_demo_db.py` (les lignes “Rows:” suffisent)
- et si les 3 requêtes UI fonctionnent

Ensuite on clôture Phase 1 et on planifie Phase 2 (NL2SQL / Ollama).

---

# Cours Phase 1 — Apprentissages clés
Tu as maintenant une **base fonctionnelle** (config + exécution SQL + UI + tests + DB démo). On va transformer ça en “cours” structuré sur :

- **SQLAlchemy**
- **Gestion de config**
- **Streamlit basics**

Je reste volontairement “pratique” : concepts + ce que tu as fait + pièges + mini-exos.

---

## 1) SQLAlchemy (les bases utiles pour ton projet)

### 1.1. À quoi sert SQLAlchemy ici ?
SQLAlchemy est une **couche d’abstraction** au-dessus des DB qui te permet :
- de te connecter à plusieurs moteurs (SQLite, Postgres, MySQL…)
- d’exécuter du SQL de manière plus propre (paramètres, transactions)
- plus tard : d’utiliser l’ORM si tu veux (pas obligatoire)

Dans Phase 1, tu utilises surtout :
- `create_engine(database_url)`
- [conn.execute(text(sql), params)](cci:1://file:///c:/Users/bello/Documents/datawizflow-ai/services/sql_executor.py:27:4-34:51)

### 1.2. Le rôle de `Engine` et `Connection`
Dans ton [SQLExecutor](cci:2://file:///c:/Users/bello/Documents/datawizflow-ai/services/sql_executor.py:15:0-34:51) :
- **`Engine`** = “usine” à connexions + gestion pool (même si SQLite est simple)
- **`Connection`** = une connexion active, utilisée dans un `with` (bonne pratique)

Pourquoi `with self._engine.connect() as conn:` ?
- garantit la fermeture propre même en cas d’erreur
- évite les connexions “pendantes”

### 1.3. `text()` et les paramètres (anti-SQL injection)
Tu fais :
```python
conn.execute(text(sql), params or {})
```

**Pourquoi `text()` ?**
- SQLAlchemy comprend que c’est une requête SQL “texte”
- tu pourras faire des requêtes paramétrées, ex :
```sql
SELECT * FROM sales WHERE region_id = :region_id
```
et côté Python :
```python
executor.execute("SELECT ... WHERE region_id=:region_id", {"region_id": 2})
```

Ça évite :
- concaténer des strings SQL (dangereux)
- les erreurs de quoting

### 1.4. `sqlite+pysqlite:///:memory:` dans les tests
**Pourquoi :memory:?**
- DB éphémère créée en RAM
- tests rapides, isolés, reproductibles
- aucun fichier généré dans [db/](cci:9://file:///c:/Users/bello/Documents/datawizflow-ai/db:0:0-0:0)

### 1.5. Mini-exos SQLAlchemy (5 min)
Dans ta page “Connexion & Sources”, essaye :
- **Exo A** : une requête paramétrée (on ajoutera le support UI plus tard)
- **Exo B** : créer une table “temp” puis vérifier qu’elle existe
  - et comprendre que SQLite persiste dans `db/demo.db`

---

## 2) Gestion de config (YAML + .env + substitution)

### 2.1. Pourquoi on a 2 niveaux de config ?
Tu as :
- [config/config.yaml](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/config/config.yaml:0:0-0:0) : **versionné**, lisible, structurel (“contrat”)
- [.env](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/.env:0:0-0:0) : **local**, non versionné, contient les valeurs (souvent sensibles)

**But :**
- tu peux partager le repo sans exposer tes secrets
- tu changes d’environnement sans changer le code

### 2.2. `${DATABASE_URL}` : le principe
Dans YAML :
```yaml
database:
  url: ${DATABASE_URL}
```

Puis ton [ConfigManager](cci:2://file:///c:/Users/bello/Documents/datawizflow-ai/services/config_manager.py:45:0-55:34) remplace `${DATABASE_URL}` par la valeur de l’environnement.

**Pourquoi c’est puissant ?**
- plus tard tu auras :
  - `${OLLAMA_URL}`
  - `${OPENAI_API_KEY}` (si un jour)
  - `${POSTGRES_PASSWORD}`, etc.
- tu gardes la structure stable, seules les valeurs changent

### 2.3. `python-dotenv`
Dans ta page Streamlit, tu fais :
```python
load_dotenv()
```

**Pourquoi ?**
- [.env](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/.env:0:0-0:0) n’est pas automatiquement lu par Python
- `load_dotenv()` injecte ces variables dans `os.environ`
- ton [ConfigManager](cci:2://file:///c:/Users/bello/Documents/datawizflow-ai/services/config_manager.py:45:0-55:34) peut ensuite lire `DATABASE_URL`

### 2.4. Bonnes pratiques (pour la suite)
- [.env-template](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/config/.env-template:0:0-0:0) = documentation des variables attendues
- [.env](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/.env:0:0-0:0) jamais commité
- [ConfigManager](cci:2://file:///c:/Users/bello/Documents/datawizflow-ai/services/config_manager.py:45:0-55:34) = point unique d’accès à la config (évite le chaos)

### 2.5. Mini-exos config (3 min)
- Change `DATABASE_URL` dans [.env](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/.env:0:0-0:0) vers :
  - `sqlite:///db/demo2.db`
- Relance le script de génération DB
- Vérifie que l’UI pointe bien sur `demo2.db`

Tu verras concrètement la séparation “code vs config”.

---

## 3) Streamlit basics (ce que tu dois maîtriser)

### 3.1. Le modèle mental Streamlit
Streamlit fonctionne en mode :
- ton script est **relancé** à chaque interaction (button, input…)
- l’UI est décrite de haut en bas

Donc tu dois penser :
- “state” (état) = `st.session_state`
- et code idempotent (ne pas recréer/dupliquer sans contrôle)

### 3.2. Multipages
En lançant :
- `streamlit run app.py`

Streamlit détecte :
- `pages/*.py` comme pages automatiques

C’est pour ça que mettre [app.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/app.py:0:0-0:0) à la racine est pratique au début.

### 3.3. Inputs et callbacks
Tu utilises :
- `st.text_area`
- `st.button`
- `st.dataframe`

**Important :**
- `st.button()` retourne `True` seulement au clic
- la logique “au clic” doit être conditionnée et robuste aux reruns

### 3.4. Gestion simple d’erreurs UI
Tu as déjà :
- `st.success(...)`
- `st.error(...)`

C’est bien : l’utilisateur voit immédiatement ce qui marche / échoue.

### 3.5. Mini-exos Streamlit (5 min)
Dans “Connexion & Sources” :
- Ajoute (toi) un `st.selectbox` qui choisit une requête “pré-définie” (ex: Top catégorie, Revenu par région) puis remplit le `text_area`.
- Tu vas apprendre :
  - rerun
  - conservation de valeur
  - (plus tard) session_state

---

# Conclusion Phase 1 (ce que tu as réellement acquis)
- **SQLAlchemy** : connexion, exécution SQL, test DB, isolation via `:memory:`
- **Config** : séparation config/secret, [.env](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/.env:0:0-0:0), substitution, reproductibilité
- **Streamlit** : multipages, interactions, reruns, UI “safe”

---

## Pour valider que le cours est acquis (question rapide)
Réponds en 3 lignes max :
1) Pourquoi on ne met pas `DATABASE_URL` en dur dans le code ?
2) À quoi sert `text()` dans SQLAlchemy ?
3) Pourquoi `:memory:` est utile pour les tests ?

Après ça, on passe à **Phase 2 : NL2SQL** (installation Ollama + premier `OllamaService.generate_sql()`).

---

## Phase 2 — Tâche 1 : Intégration Ollama (Windows)

Objectif : avoir **Ollama qui tourne**, le modèle **mistral** téléchargé, et un **appel Python** qui répond. C’est le socle de tout NL2SQL.

---

# 1) Installer Ollama (moteur LLM local)

## Pourquoi ?
- Ollama = “serveur local” qui expose une API HTTP (`/api/chat`, `/api/generate`).
- Ton app Python/Streamlit n’aura qu’à appeler cette API.

## Action (toi)
Choisis une méthode :

### Option A — Installer via le site (le plus simple)
- Télécharge et installe : https://ollama.com/download/windows

### Option B — `winget` (si tu l’utilises)
```powershell
winget install Ollama.Ollama
```

## Vérification
Après installation, dans PowerShell :
```powershell
ollama --version
```

---

# 2) Démarrer le service Ollama

## Pourquoi ?
- Le serveur doit tourner pour que Python puisse l’appeler.

## Action (toi)
En général sur Windows, Ollama démarre en service automatiquement.
Vérifie que l’API répond :

```powershell
curl http://localhost:11434/api/tags
```

Attendu : un JSON (même si la liste est vide au début).

---

# 3) Télécharger un modèle (mistral)

## Pourquoi ?
- Sans modèle “pull”, Ollama ne peut rien générer.

## Action (toi)
```powershell
ollama pull mistral
```

Puis vérifie :
```powershell
ollama list
```

---

# 4) Ajouter le client Python Ollama au projet

Tu as choisi en Phase 1 un [requirements.txt](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/requirements.txt:0:0-0:0) minimal, donc **ollama n’est probablement pas installé côté Python**.

## Pourquoi ?
- On veut un petit client Python simple qui appelle l’API proprement.

## Action (toi)
1) Ajoute dans [requirements.txt](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/requirements.txt:0:0-0:0) :
```txt
ollama==0.1.0
```

2) Installe :
```powershell
pip install -r requirements.txt
```

---

# 5) Test Python (appel simple)

## Pourquoi ?
- Valider “de bout en bout” : Python -> HTTP -> Ollama -> modèle -> réponse.

## Action (toi) : crée un fichier `scripts/test_ollama.py`
```python
from ollama import Client

client = Client(base_url="http://localhost:11434")

resp = client.chat(
    model="mistral",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Réponds uniquement: OK OLLAMA"},
    ],
)

print(resp["message"]["content"])
```

Puis exécute :
```powershell
python scripts/test_ollama.py
```

Attendu : `OK OLLAMA` (ou quelque chose de très proche).

---

# 6) (Recommandé) Mettre Ollama dans [.env](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/.env:0:0-0:0)

## Pourquoi ?
- Ça évite de “hardcoder” `localhost` et le nom du modèle.
- Plus tard tu pourras passer en Docker (`http://ollama:11434`) sans toucher au code.

## Action (toi) : dans [.env](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/.env:0:0-0:0) ajoute
```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

---

## Dis-moi où ça bloque (ou si tout est OK)
Réponds avec :
- la sortie de `ollama list`
- et la sortie de `python scripts/test_ollama.py`

Ensuite on passe à **Phase 2 — Tâche suivante** : implémenter `OllamaService.generate_sql()` + première page NL2SQL sur ta DB démo.

---
Je vais ajouter un service dédié `OllamaService` dans [services/](cci:9://file:///c:/Users/bello/Documents/datawizflow-ai/services:0:0-0:0) avec une méthode `generate_sql()` qui :
- lit `OLLAMA_URL` / `OLLAMA_MODEL` (ou paramètres)
- construit un prompt NL2SQL (avec le schéma SQLite de ta DB démo + règles read-only)
- appelle Ollama via le client Python `ollama`
- nettoie la réponse (retire les ``` et renvoie uniquement le SQL)

Je commence par vérifier ce qui existe déjà dans [services/](cci:9://file:///c:/Users/bello/Documents/datawizflow-ai/services:0:0-0:0) pour ne rien écraser.






## [OllamaService.generate_sql()](cci:1://file:///c:/Users/bello/Documents/datawizflow-ai/services/ollama_service.py:111:4-133:26) implémenté

J’ai créé un nouveau fichier **[services/ollama_service.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/services/ollama_service.py:0:0-0:0)** (car il n’existait pas) avec :

- **[OllamaService.generate_sql(question, language="FR", schema=None)](cci:1://file:///c:/Users/bello/Documents/datawizflow-ai/services/ollama_service.py:111:4-133:26)**
  - construit un prompt NL2SQL **read-only**
  - injecte le **schéma** de ta DB SQLite (auto si tu fournis [database_url](cci:1://file:///c:/Users/bello/Documents/datawizflow-ai/services/config_manager.py:36:4-42:18))
  - appelle Ollama via `ollama.Client(base_url=...)`
  - nettoie la réponse (retire les fences ```sql``` si besoin) et renvoie **uniquement le SQL**

### Pourquoi un service séparé ?
- **Séparation des responsabilités** :
  - [SQLExecutor](cci:2://file:///c:/Users/bello/Documents/datawizflow-ai/services/sql_executor.py:15:0-34:51) = exécution SQL
  - [OllamaService](cci:2://file:///c:/Users/bello/Documents/datawizflow-ai/services/ollama_service.py:64:0-133:26) = génération SQL via LLM
- Ça rend testable et réutilisable (page NL2SQL, DataViz plus tard, etc.)

---

# 1) Pré-requis (à vérifier côté toi)
Dans [.env](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/.env:0:0-0:0), tu devrais avoir (ou ajouter) :
```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral
DATABASE_URL=sqlite:///db/demo.db
```

---

# 2) Test rapide (avant UI NL2SQL)

## Action (toi) : créer `scripts/test_generate_sql.py`
```python
from dotenv import load_dotenv

from services.config_manager import ConfigManager
from services.ollama_service import OllamaService

load_dotenv()

cfg = ConfigManager().load()

svc = OllamaService(database_url=cfg.database_url)

sql = svc.generate_sql(
    question="Donne le chiffre d'affaires total par catégorie",
    language="FR",
)

print(sql)
```

Puis exécute :
```powershell
python scripts/test_generate_sql.py
```

Pourquoi ``python scripts/test_generate_sql.py`` ne trouve pas services ?
Quand tu exécutes un fichier dans un sous-dossier comme ça :

```powershell
python scripts/test_generate_sql.py
```

Python met `scripts/` comme “répertoire de départ” pour les imports (`sys.path[0] = .../scripts`). Du coup, il ne voit pas `services/` qui est à la racine.

Dans `pytest`, ça marchait parce qu’on avait ajouté `tests/conftest.py` qui injecte la racine du projet dans le `sys.path`. Ici, on n’a pas cet aide.

Solution recommandée (pédagogique) : exécuter en module `-m`
Lance plutôt :

```powershell
python -m scripts.test_generate_sql
```

Pourquoi ça marche ?
En mode module (-m), Python considère la racine du projet comme base d’import, donc from services... devient importable.

> Optionnel : tu peux aussi créer un fichier vide `scripts/__init__.py` (pas obligatoire dans les versions récentes, mais propre).



### Attendu
Un SQL du type :
```sql
SELECT p.category, SUM(s.revenue) ...
FROM sales s JOIN products p ...
GROUP BY p.category;
```

---

# 3) Petit point d’attention (important)
Le prompt interdit `PRAGMA`, `CREATE`, etc. C’est volontaire pour éviter des requêtes dangereuses.

Mais :
- SQLite supporte plein de choses
- on renforcera ça en **Phase 2 / Prompt engineering** + validation côté exécution (read-only) dans la prochaine tâche.

---

# Prochaine étape (après test OK)
On passe à **Phase 2 — Tâche 2/3** :
- construire le **template de prompt** propre (FR/EN) avec exemples
- puis créer la **page Streamlit NL2SQL** (zone NL, bouton générer, SQL éditable, exécuter, résultats)

Dis-moi :
- la sortie de `python scripts/test_generate_sql.py`
- et si Ollama renvoie bien du SQL propre (sans explication).

---

## Phase 2 — Tâche 2 : Prompt engineering (NL2SQL)

Objectif : obtenir un prompt **stable** qui force Ollama à produire du SQL :
- **correct pour SQLite**
- **strictement read-only**
- **sans blabla, sans markdown**
- **robuste** (même si le modèle “veut expliquer”)

Je te propose une approche en 3 couches : **règles**, **schéma**, **format de sortie** + **exemples**.

---

# 1) Spécification (contrat) du SQL attendu

## Pourquoi ?
Si tu ne définis pas un “contrat de sortie”, le LLM va souvent :
- ajouter des explications
- renvoyer du markdown
- inventer des colonnes/tables
- proposer du DDL (`CREATE`, `DROP`, etc.)

## Contrat de sortie (à imposer)
- **Retourner uniquement** une requête SQL.
- **Une seule requête** (un seul statement).
- **Read-only** : autoriser uniquement `SELECT` (+ `WITH` pour CTE si tu veux), `JOIN`, `GROUP BY`, `ORDER BY`, `LIMIT`.
- **Interdire** : `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `PRAGMA`, `ATTACH`, `DETACH`, `VACUUM`, `REINDEX`, `TRUNCATE`.
- Ajouter un **`LIMIT 200`** si la question ne demande pas explicitement “tout”.
- Si la question est ambiguë : choisir l’interprétation la plus raisonnable **sans poser de question** (ou retourner un `SELECT` simple).

---

# 2) Template de prompt FR/EN (copier/coller)

Tu peux soit intégrer ça dans [OllamaService.build_prompt](cci:1://file:///c:/Users/bello/Documents/datawizflow-ai/services/ollama_service.py:81:4-109:9), soit créer un module dédié (ex: `utils/prompts.py`). Comme tu veux apprendre, je te donne le template “pur”.

## FR — Prompt template
```text
RÔLE:
Tu es un expert SQL pour SQLite.

OBJECTIF:
Générer UNE SEULE requête SQL pour répondre à la question de l’utilisateur.

CONTRAINTES STRICTES:
- La requête DOIT être read-only.
- Requête autorisée: uniquement SELECT (CTE WITH autorisée).
- Interdit: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA, ATTACH, DETACH, VACUUM, REINDEX, TRUNCATE.
- N'invente jamais des tables ou des colonnes.
- Utilise uniquement les tables/colonnes présentes dans le schéma.
- Retourne uniquement le SQL, sans explication, sans commentaires, sans markdown, sans triple backticks.
- Si la question ne demande pas explicitement "tout", ajoute LIMIT 200 si aucun LIMIT n'est présent.

SCHÉMA DE LA BASE:
{schema}

EXEMPLES:
Q: Chiffre d'affaires total par catégorie
SQL:
SELECT p.category, SUM(s.revenue) AS revenue_total
FROM sales s
JOIN products p ON p.product_id = s.product_id
GROUP BY p.category
ORDER BY revenue_total DESC
LIMIT 200;

Q: Revenu total par région
SQL:
SELECT r.region_name, SUM(s.revenue) AS revenue_total
FROM sales s
JOIN regions r ON r.region_id = s.region_id
GROUP BY r.region_name
ORDER BY revenue_total DESC
LIMIT 200;

QUESTION UTILISATEUR:
{question}

SQL:
```

## EN — Prompt template
```text
ROLE:
You are an expert SQL engineer for SQLite.

GOAL:
Generate ONE SQL query that answers the user's question.

STRICT CONSTRAINTS:
- The query MUST be read-only.
- Allowed: SELECT only (WITH CTE allowed).
- Forbidden: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA, ATTACH, DETACH, VACUUM, REINDEX, TRUNCATE.
- Never invent tables or columns.
- Use only the tables/columns from the schema.
- Output ONLY the SQL. No explanation, no comments, no markdown, no triple backticks.
- If the question does not explicitly ask for "all rows", add LIMIT 200 if no LIMIT is present.

DATABASE SCHEMA:
{schema}

EXAMPLES:
Q: Total revenue by category
SQL:
SELECT p.category, SUM(s.revenue) AS revenue_total
FROM sales s
JOIN products p ON p.product_id = s.product_id
GROUP BY p.category
ORDER BY revenue_total DESC
LIMIT 200;

Q: Total revenue by region
SQL:
SELECT r.region_name, SUM(s.revenue) AS revenue_total
FROM sales s
JOIN regions r ON r.region_id = s.region_id
GROUP BY r.region_name
ORDER BY revenue_total DESC
LIMIT 200;

USER QUESTION:
{question}

SQL:
```

---

# 3) Ajout “anti-dérapage” côté code (à faire ensuite)
Même avec un bon prompt, il faut **valider** la sortie du modèle avant exécution.

## Règles de validation à implémenter (prochaine sous-étape)
- SQL doit commencer par `SELECT` ou `WITH`
- Refuser si contient un mot interdit (regex simple sur mots-clés)
- Refuser si contient `;` et qu’il y a plus d’un statement (tu peux faire simple au début : refuser tout `;`)

> On fera ça dans la prochaine tâche (Interface NL2SQL), juste avant l’exécution.

---

# 4) Jeu de tests (questions à essayer)
Avec ton schéma `sales/products/regions/dates`, teste ces questions :

- **FR1**: “Top 5 produits par revenu total”
- **FR2**: “Revenu total par mois (2024)”
- **FR3**: “Revenu moyen par vente par catégorie”
- **FR4**: “Quantité totale vendue par région”
- **FR5**: “Les 10 jours avec le plus gros revenu”

Attendu (approximatif) : joins corrects + `GROUP BY` + `ORDER BY` + `LIMIT`.

---

# Question pour toi (pour décider du prochain pas)
Tu veux faire le prompt engineering :
- **Option A**: tu modifies directement [services/ollama_service.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/services/ollama_service.py:0:0-0:0) (la méthode [build_prompt](cci:1://file:///c:/Users/bello/Documents/datawizflow-ai/services/ollama_service.py:81:4-109:9)) avec ce template
- **Option B**: tu crées un module dédié `utils/nl2sql_prompts.py` (plus propre, plus testable), et [OllamaService](cci:2://file:///c:/Users/bello/Documents/datawizflow-ai/services/ollama_service.py:64:0-133:26) l’utilise

Dis-moi `A` ou `B`, et je te donne exactement quoi modifier/créer (toujours en te laissant exécuter les actions toi-même).

---
## Option B — Module dédié `utils/nl2sql_prompts.py` (prompt engineering propre et testable)

### Pourquoi Option B est meilleure ?
- **Séparation claire** :
  - `utils/nl2sql_prompts.py` = *prompt engineering* (texte + règles + exemples)
  - [services/ollama_service.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/services/ollama_service.py:0:0-0:0) = *appel Ollama + orchestration*
- **Testabilité** : tu peux tester le prompt sans dépendre d’Ollama.
- **Évolutivité** : quand tu passeras à d’autres DB (Postgres), tu changes surtout le prompt et la description de schéma.

---

# 1) Action (toi) : créer `utils/nl2sql_prompts.py`

Crée le fichier `utils/nl2sql_prompts.py` et colle ceci :

```python
from __future__ import annotations


def build_nl2sql_prompt(*, question: str, schema: str, language: str = "FR") -> str:
    lang = (language or "FR").upper()
    if lang not in {"FR", "EN"}:
        lang = "EN"

    if lang == "FR":
        return f"""RÔLE:
Tu es un expert SQL pour SQLite.

OBJECTIF:
Générer UNE SEULE requête SQL pour répondre à la question de l’utilisateur.

CONTRAINTES STRICTES:
- La requête DOIT être read-only.
- Requête autorisée: uniquement SELECT (CTE WITH autorisée).
- Interdit: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA, ATTACH, DETACH, VACUUM, REINDEX, TRUNCATE.
- N'invente jamais des tables ou des colonnes.
- Utilise uniquement les tables/colonnes présentes dans le schéma.
- Retourne uniquement le SQL, sans explication, sans commentaires, sans markdown, sans triple backticks.
- Si la question ne demande pas explicitement "tout", ajoute LIMIT 200 si aucun LIMIT n'est présent.

SCHÉMA DE LA BASE:
{schema}

EXEMPLES:
Q: Chiffre d'affaires total par catégorie
SQL:
SELECT p.category, SUM(s.revenue) AS revenue_total
FROM sales s
JOIN products p ON p.product_id = s.product_id
GROUP BY p.category
ORDER BY revenue_total DESC
LIMIT 200;

Q: Revenu total par région
SQL:
SELECT r.region_name, SUM(s.revenue) AS revenue_total
FROM sales s
JOIN regions r ON r.region_id = s.region_id
GROUP BY r.region_name
ORDER BY revenue_total DESC
LIMIT 200;

QUESTION UTILISATEUR:
{question}

SQL:"""
    else:
        return f"""ROLE:
You are an expert SQL engineer for SQLite.

GOAL:
Generate ONE SQL query that answers the user's question.

STRICT CONSTRAINTS:
- The query MUST be read-only.
- Allowed: SELECT only (WITH CTE allowed).
- Forbidden: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA, ATTACH, DETACH, VACUUM, REINDEX, TRUNCATE.
- Never invent tables or columns.
- Use only the tables/columns from the schema.
- Output ONLY the SQL. No explanation, no comments, no markdown, no triple backticks.
- If the question does not explicitly ask for "all rows", add LIMIT 200 if no LIMIT is present.

DATABASE SCHEMA:
{schema}

EXAMPLES:
Q: Total revenue by category
SQL:
SELECT p.category, SUM(s.revenue) AS revenue_total
FROM sales s
JOIN products p ON p.product_id = s.product_id
GROUP BY p.category
ORDER BY revenue_total DESC
LIMIT 200;

Q: Total revenue by region
SQL:
SELECT r.region_name, SUM(s.revenue) AS revenue_total
FROM sales s
JOIN regions r ON r.region_id = s.region_id
GROUP BY r.region_name
ORDER BY revenue_total DESC
LIMIT 200;

USER QUESTION:
{question}

SQL:"""
```

---

# 2) Action (toi) : modifier [services/ollama_service.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/services/ollama_service.py:0:0-0:0) pour utiliser ce module

Dans [services/ollama_service.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/services/ollama_service.py:0:0-0:0) :

## A) Ajoute l’import en haut
```python
from utils.nl2sql_prompts import build_nl2sql_prompt
```

## B) Simplifie [build_prompt(...)](cci:1://file:///c:/Users/bello/Documents/datawizflow-ai/services/ollama_service.py:81:4-109:9)
Tu peux soit supprimer la méthode actuelle, soit la garder mais la faire déléguer.

Le plus simple (pédagogique) : remplacer le contenu de [build_prompt](cci:1://file:///c:/Users/bello/Documents/datawizflow-ai/services/ollama_service.py:81:4-109:9) par :

```python
def build_prompt(self, *, question: str, schema: str, language: str) -> str:
    return build_nl2sql_prompt(question=question, schema=schema, language=language)
```

## C) Dans [generate_sql(...)](cci:1://file:///c:/Users/bello/Documents/datawizflow-ai/services/ollama_service.py:111:4-133:26), garde le reste identique
Il doit continuer à faire :
- `schema_text = _describe_sqlite_schema(...)` si `schema` est `None`
- [prompt = self.build_prompt(...)](cci:1://file:///c:/Users/bello/Documents/datawizflow-ai/services/ollama_service.py:81:4-109:9)
- appel `self._client.chat(...)`
- nettoyage [_strip_code_fences(...)](cci:1://file:///c:/Users/bello/Documents/datawizflow-ai/services/ollama_service.py:15:0-19:23)

---

# 3) Test (toi) : retester la génération SQL

1) Corrige le `.` final dans [scripts/test_generate_sql.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/scripts/test_generate_sql.py:0:0-0:0) si tu l’as encore (`print(sql).` → `print(sql)`).
2) Exécute en mode module (important pour les imports) :

```powershell
python -m scripts.test_generate_sql
```

---

## Ce que je veux que tu me colles ensuite
- Le SQL généré pour :
  - “Top 5 produits par revenu total”
  - “Revenu total par mois (2024)”

À partir de là, on pourra :
- ajuster les exemples dans le prompt si nécessaire
- puis passer à **Phase 2 — Tâche 3 : Interface NL2SQL** (page Streamlit, génération + édition + exécution + résultats).

---

## Nickel — le prompt engineering marche
On voit bien l’amélioration entre les 2 runs :

- **Run 1** : SQL correct mais sans `LIMIT`, alias “TotalRevenue” un peu arbitraire.
- **Run 2** : SQL *propre*, joins explicites, `ORDER BY`, `LIMIT 200` ✅

Ça valide que le **module [utils/nl2sql_prompts.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/utils/nl2sql_prompts.py:0:0-0:0) + exemples** influence bien le modèle.

---

# Prochaine étape logique : Phase 2 — Tâche 3 (Interface NL2SQL Streamlit)
On va faire une page `pages/2_NL2SQL.py` qui permet :

- **Entrée NL** (question)
- bouton **Générer SQL** (via [OllamaService.generate_sql](cci:1://file:///c:/Users/bello/Documents/datawizflow-ai/services/ollama_service.py:111:4-133:26))
- zone **SQL éditable**
- bouton **Exécuter** (via [SQLExecutor.execute](cci:1://file:///c:/Users/bello/Documents/datawizflow-ai/services/sql_executor.py:27:4-34:51))
- affichage des résultats en `dataframe`
- exports CSV / Excel (Excel optionnel si tu veux rester minimal)

## Mais avant : 2 petites décisions (pour apprendre correctement)

### 1) Tu veux la validation read-only maintenant ou juste après ?
- **Option A (recommandé)** : on ajoute tout de suite une validation simple avant exécution
  - autoriser seulement `SELECT` / `WITH`
  - refuser mots-clés dangereux
  - forcer `LIMIT` si absent
- **Option B** : on fait l’UI d’abord “brute”, puis on sécurise à la tâche suivante

### 2) Résultats : tu veux une limite UI (pagination simple) ?
- **Option A** : on affiche tout (mais la requête a déjà `LIMIT 200`)
- **Option B** : on ajoute un select “limit 50/200/1000” côté UI

Réponds :
- `1A` ou `1B`
- `2A` ou `2B`

Ensuite je te donne **le code exact** à créer dans `pages/2_NL2SQL.py` (et les imports nécessaires) et tu l’ajoutes toi-même.

---


## Parfait — `1A` (validation maintenant) + `2B` (limit UI)

On va créer **2 fichiers** :

- `utils/sql_safety.py`  
  - contient la **validation read-only** + ajout automatique de `LIMIT`
- `pages/2_NL2SQL.py`  
  - page Streamlit NL2SQL : question NL → génération SQL → édition → exécution → résultats + export CSV

Je te donne **quoi créer / quoi coller** (tu fais les actions).

---

# 1) Action (toi) — créer `utils/sql_safety.py`

## Pourquoi on le crée ?
- Séparer la **sécurité SQL** de l’UI Streamlit.
- Réutilisable plus tard (DataViz, historique, etc.).
- Testable via pytest.

## Contenu à coller
```python
from __future__ import annotations

import re


_FORBIDDEN = [
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "pragma",
    "attach",
    "detach",
    "vacuum",
    "reindex",
    "truncate",
]

_FORBIDDEN_RE = re.compile(r"\b(" + "|".join(_FORBIDDEN) + r")\b", re.IGNORECASE)
_LIMIT_RE = re.compile(r"\blimit\b", re.IGNORECASE)


def validate_readonly_sql(sql: str) -> None:
    if not sql or not sql.strip():
        raise ValueError("SQL vide")

    s = sql.strip().lstrip("(").strip()

    # Only SELECT / WITH allowed
    if not (s.lower().startswith("select") or s.lower().startswith("with")):
        raise ValueError("Seules les requêtes SELECT/WITH sont autorisées (read-only).")

    # Simple multi-statement protection
    # (au début on reste strict : refuse tout ';' pour éviter 'SELECT...; DROP ...')
    if ";" in s:
        raise ValueError("Les requêtes multi-statements sont interdites (retire le ';').")

    # Forbidden keywords
    m = _FORBIDDEN_RE.search(s)
    if m:
        raise ValueError(f"Mot-clé interdit détecté: {m.group(1)}")


def ensure_limit(sql: str, limit: int) -> str:
    s = sql.strip()
    if _LIMIT_RE.search(s):
        return s
    return f"{s}\nLIMIT {int(limit)}"
```

---

# 2) Action (toi) — créer `pages/2_NL2SQL.py`

## Pourquoi on le crée ?
- C’est l’interface centrale de Phase 2 :
  - transformer une question en SQL
  - te laisser contrôler le SQL (édition)
  - exécuter et visualiser les résultats

## Contenu à coller
```python
import io

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from services.config_manager import ConfigManager
from services.ollama_service import OllamaService
from services.sql_executor import SQLExecutor
from utils.sql_safety import ensure_limit, validate_readonly_sql

load_dotenv()

st.title("NL2SQL")

cfg = ConfigManager().load()

executor = SQLExecutor(cfg.database_url)
ollama = OllamaService(database_url=cfg.database_url)

with st.sidebar:
    st.header("NL2SQL Settings")
    language = st.selectbox("Language", ["FR", "EN"], index=0, key="nl2sql_language")
    model_info = f"{ollama.settings.model} @ {ollama.settings.base_url}"
    st.caption(f"Ollama: {model_info}")

    limit = st.selectbox("LIMIT", [50, 200, 1000], index=1, key="nl2sql_limit")


st.subheader("Question (langage naturel)")
question = st.text_area(
    "Question",
    value=st.session_state.get("nl2sql_question", ""),
    height=100,
    placeholder="Ex: Donne le chiffre d'affaires total par catégorie",
)
st.session_state["nl2sql_question"] = question

col_a, col_b = st.columns([1, 1])
with col_a:
    if st.button("Générer SQL", disabled=not bool(question.strip())):
        try:
            sql_generated = ollama.generate_sql(question=question, language=language)
            st.session_state["nl2sql_sql"] = sql_generated
            st.success("SQL généré")
        except Exception as e:
            st.error(str(e))

with col_b:
    if st.button("Effacer"):
        st.session_state["nl2sql_question"] = ""
        st.session_state["nl2sql_sql"] = ""
        st.session_state["nl2sql_df"] = None


st.subheader("SQL (éditable)")
sql_text = st.text_area(
    "SQL",
    value=st.session_state.get("nl2sql_sql", ""),
    height=180,
    placeholder="Le SQL généré apparaîtra ici…",
)
st.session_state["nl2sql_sql"] = sql_text


st.subheader("Exécution")
if st.button("Valider + Exécuter", disabled=not bool(sql_text.strip())):
    try:
        validate_readonly_sql(sql_text)
        sql_to_run = ensure_limit(sql_text, limit=int(limit))
        res = executor.execute(sql_to_run)

        df = pd.DataFrame(res.rows, columns=res.columns) if res.columns else pd.DataFrame()
        st.session_state["nl2sql_df"] = df
        st.session_state["nl2sql_sql_executed"] = sql_to_run
        st.success("Exécution OK")
    except Exception as e:
        st.error(str(e))


df = st.session_state.get("nl2sql_df")
sql_executed = st.session_state.get("nl2sql_sql_executed")

if sql_executed:
    st.caption("SQL exécuté :")
    st.code(sql_executed, language="sql")

if df is not None:
    st.subheader("Résultats")
    st.caption(f"Lignes: {len(df)}")
    st.dataframe(df, use_container_width=True)

    st.subheader("Export")
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button("Télécharger CSV", data=csv_bytes, file_name="nl2sql_result.csv", mime="text/csv")
```

---

# 3) Test (toi)

1) Relance Streamlit :
```powershell
streamlit run app.py
```

2) Va dans la page **NL2SQL**

3) Tests à faire :
- Question : **“Top 5 produits par revenu total”**
- Puis clique :
  - **Générer SQL**
  - **Valider + Exécuter**
- Change le `LIMIT` sidebar (50/200/1000) et observe.

---

# 4) Ce que tu me colles ensuite
- Le SQL généré pour “Top 5 produits par revenu total”
- Le résultat (au moins 2 lignes)
- Et si tu as eu un blocage sur la validation (message exact)

---

## Statut
- **Prompt engineering : OK**
- On démarre **Tâche 3 Interface NL2SQL** avec validation read-only intégrée et limite UI (comme tu l’as choisi).

---

## Résultat : OK (NL2SQL → SQL → exécution)

Ton SQL est **excellent** :
- `JOIN` correct (`sales` ↔ `products`)
- agrégation correcte `SUM(s.revenue)`
- tri décroissant + `LIMIT 5`

Et le tableau de résultats est cohérent (les laptops dominent, logique vu les prix/unités).

---

# 1) Petit point “qualité des données” (float)
Tu vois `112818.15000000002` : c’est normal, c’est l’effet des **floats**.

## Option (si tu veux un affichage plus propre)
Dans le SQL, tu peux arrondir :
```sql
SELECT p.product_name, ROUND(SUM(s.revenue), 2) AS revenue_total
...
```
On peut aussi arrondir côté pandas, mais SQL est plus simple.

---

# 2) Sécurité : tu as un bug à corriger (les `.` finaux)
Je vois dans les fichiers créés :
- [utils/sql_safety.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/utils/sql_safety.py:0:0-0:0) finit par `return f"..."\nLIMIT ...".` (un point final)
- [pages/2_NL2SQL.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/pages/2_NL2SQL.py:0:0-0:0) finit par `mime="text/csv").` (point final)

Ça peut provoquer un **SyntaxError** (ou casser au chargement Streamlit) dès que tu relances.

## Action (toi)
- Dans [utils/sql_safety.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/utils/sql_safety.py:0:0-0:0) : dernière ligne → enlève le `.` final
  - doit finir par :
  - `return f"{s}\nLIMIT {int(limit)}"`
- Dans [pages/2_NL2SQL.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/pages/2_NL2SQL.py:0:0-0:0) : enlève le `.` final de la dernière ligne `st.download_button(...)`

---

# 3) Étape suivante (Phase 2) : compléter “Affichage des résultats” + Exports
Tu as déjà :
- affichage dataframe ✅
- export CSV ✅

Deux améliorations utiles (tu choisis) :
- **A)** Export Excel (nécessite `openpyxl` dans [requirements.txt](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/requirements.txt:0:0-0:0))
- **B)** Ajout d’un bloc “requêtes exemples” (selectbox) pour apprendre et tester rapidement

Réponds `A`, `B` ou `A+B`, et je te donne les étapes exactes (toujours exécutées par toi).

## Statut
- **Interface NL2SQL de base : validée**
- Prochaine action recommandée immédiate : **retirer les `.` finaux** pour stabiliser.

---


## OK — on fait `A+B` (Export Excel + Requêtes exemples) + on corrige les `.` finaux

Je te propose l’ordre **le plus safe** :
1) Corriger les `.` finaux (sinon risque de crash au reload)
2) Ajouter `openpyxl` (Excel)
3) Ajouter “Requêtes exemples” (selectbox) + exports CSV/Excel

---

# 0) Correction immédiate : enlever les `.` finaux

## Pourquoi ?
Un `.` à la fin d’une ligne Python rend le fichier **invalide** → `SyntaxError` au prochain reload Streamlit.

## Action (toi)

### A) [utils/sql_safety.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/utils/sql_safety.py:0:0-0:0)
La dernière ligne doit être exactement :
```python
return f"{s}\nLIMIT {int(limit)}"
```
(sans `.` à la fin)

### B) [pages/2_NL2SQL.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/pages/2_NL2SQL.py:0:0-0:0)
La dernière ligne `st.download_button(...)` doit finir par `)` uniquement (pas `).`)

---

# 1) Export Excel (A) — ajouter la dépendance

## Pourquoi ?
Pandas écrit en Excel via un “engine”. Pour `.xlsx`, le plus courant = `openpyxl`.

## Action (toi) : [requirements.txt](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/requirements.txt:0:0-0:0)
Ajoute :
```txt
openpyxl==3.1.5
```

Puis installe :
```powershell
pip install -r requirements.txt
```

---

# 2) Requêtes exemples (B) + Exports CSV/Excel dans la page NL2SQL

## Pourquoi ?
- Les exemples te servent de **bootstrap** pour apprendre et tester vite.
- L’export Excel est très demandé en usage “BI”.

## Action (toi) : modifier [pages/2_NL2SQL.py](cci:7://file:///c:/Users/bello/Documents/datawizflow-ai/pages/2_NL2SQL.py:0:0-0:0)

### A) Ajoute un bloc “Exemples” *juste avant* le `st.text_area` de la question
Colle ce bloc après `limit = st.selectbox(...)` (dans la sidebar par exemple) :

```python
examples = {
    "—": "",
    "Top 5 produits par revenu": """SELECT p.product_name, ROUND(SUM(s.revenue), 2) AS revenue_total
FROM sales s
JOIN products p ON p.product_id = s.product_id
GROUP BY p.product_name
ORDER BY revenue_total DESC
LIMIT 5""",
    "Revenu total par catégorie": """SELECT p.category, ROUND(SUM(s.revenue), 2) AS revenue_total
FROM sales s
JOIN products p ON p.product_id = s.product_id
GROUP BY p.category
ORDER BY revenue_total DESC""",
    "Revenu total par région": """SELECT r.region_name, ROUND(SUM(s.revenue), 2) AS revenue_total
FROM sales s
JOIN regions r ON r.region_id = s.region_id
GROUP BY r.region_name
ORDER BY revenue_total DESC""",
    "Revenu total par mois (2024)": """SELECT d.year, d.month, ROUND(SUM(s.revenue), 2) AS revenue_total
FROM sales s
JOIN dates d ON d.date = s.sale_date
GROUP BY d.year, d.month
ORDER BY d.year, d.month""",
}

with st.sidebar:
    st.subheader("Exemples")
    example_name = st.selectbox("Charger un exemple", list(examples.keys()), index=0)
    if st.button("Charger l'exemple", disabled=(example_name == "—")):
        st.session_state["nl2sql_sql"] = examples[example_name]
```

### B) Export Excel (ajoute après l’export CSV)
Dans ton bloc `if df is not None:` après le CSV, ajoute :

```python
excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="results")

st.download_button(
    "Télécharger Excel",
    data=excel_buffer.getvalue(),
    file_name="nl2sql_result.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
```

> Note : tu as déjà `import io` en haut, donc c’est parfait.

---

# 3) Test (toi)
1) Relance Streamlit :
```powershell
streamlit run app.py
```

2) Va dans **NL2SQL**
- Clique “Charger l’exemple” (ex: Revenu total par région)
- Clique “Valider + Exécuter”
- Télécharge **CSV** puis **Excel** et ouvre l’Excel pour vérifier.

---

## Dis-moi le résultat
- Est-ce que le bouton Excel apparaît bien ?
- Est-ce que le fichier `.xlsx` s’ouvre correctement ?
- Et confirme que le “Charger l’exemple” remplit bien la zone SQL.

Ensuite on pourra attaquer la suite du plan Phase 2 :
- **Historique & sauvegarde** (SQLite interne)
- **Tests** `test_generate_sql_simple()` + `test_execute_query()` + test d’intégration.

---
