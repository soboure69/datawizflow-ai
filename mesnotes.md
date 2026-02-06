
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
