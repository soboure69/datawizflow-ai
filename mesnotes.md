
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
