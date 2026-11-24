# Aptus - Plateforme Web Recrutement, Formations & Intelligence Marché (Django)

Cette application est la refonte complète et modulaire en **Python / Django** avec base de données **SQLite** de l'ancien projet PHP `aptus_first_official_version`.

---

## 🚀 Architecture Modulaire

L'application couvre l'ensemble des modules CRUD métier :

- **`accounts`** : Gestion des utilisateurs (`Utilisateur`), profils et sous-rôles (`Administrateur`, `Candidat`, `Entreprise`).
- **`jobs`** : Gestion des offres d'emploi (`OffreEmploi`) et du cycle de vie des candidatures (`Candidature`).
- **`cv_studio`** : Gestion des CVs (`CV`), modèles de mise en page (`Template`), audits IA (`RapportIA`) et guides de recrutement (`GuideRecrutement`).
- **`training`** : Formations (`Formation`), affectation des tuteurs et suivi des inscriptions (`Inscription`).
- **`market`** : Veille économique, rapports sectoriels (`RapportMarche`) et statistiques de rémunération (`DonneeMarche`).

---

## 🛠️ Démarrage Rapide

### 1. Prérequis
- Python 3.10+ installé.
- Ouvrir un terminal dans ce dossier :
  ```bash
  cd "C:\Users\outheila\Downloads\aptus"
  ```

### 2. Installation des dépendances (Optionnel si Django est déjà installé globalement)
```bash
pip install -r requirements.txt
```

### 3. Lancer le serveur de développement
```bash
python manage.py runserver
```

---

## 🌐 Liens d'Accès

- **Application Web & Tableaux de bord** : [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Administration Django** : [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
  - **Identifiant** : `admin`
  - **Mot de passe** : `admin`

---

## 📂 Structure du Projet

```
aptus/
├── accounts/           # Utilisateurs & Authentification
├── jobs/               # Offres & Candidatures
├── cv_studio/          # CVs, Templates & Rapports IA
├── training/           # Formations & Inscriptions
├── market/             # Veille Marché & Salaires
├── aptus_core/         # Configuration globale & URLs
├── templates/          # Templates HTML Django (Bootstrap 5)
├── static/             # Fichiers CSS, JS et images
├── db.sqlite3          # Base de données SQLite pré-remplie
├── manage.py           # CLI Django
└── seed_data.py        # Script de peuplement de données
```
