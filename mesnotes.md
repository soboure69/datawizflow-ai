
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
