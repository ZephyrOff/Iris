<p align="center">
  <img src="Iris/static/asset/iris_logo.png" alt="logo"/>
</p>

# Iris

Ce projet est un worker d'API conçu pour gérer diverses requêtes API, traiter des données et interagir avec des services externes. Il offre une solution robuste et évolutive pour la gestion des flux de travail API.

## Fonctionnalités

*   **Gestion des requêtes API** : Traite efficacement les requêtes API entrantes.
*   **Traitement des données** : Inclut des modules pour la manipulation et la transformation des données.
*   **Intégration de services externes** : Conçu pour interagir de manière transparente avec diverses API et services externes.
*   **Évolutivité** : Conçu pour être évolutif afin de gérer des charges croissantes.
*   **Gestion des erreurs** : Gestion robuste des erreurs pour assurer la stabilité de l'application.
*   **Journalisation** : Système de journalisation complet pour la surveillance et le débogage.
*   **Authentification et Autorisation** : Authentification sécurisée des utilisateurs et gestion des jetons API.
*   **Panneau d'administration** : Interface web pour la gestion des utilisateurs, des jetons API et la consultation des journaux.

## Technologies Utilisées

*   **Backend** : Python, Flask (waitress en mode prod)
*   **Base de données** : SQLite (par défaut, configurable)
*   **Frontend** : HTML, CSS, JavaScript
*   **Authentification** : Système interne
*   **Sécurité** : Système interne de Fail2Ban

## Configuration et Installation

Suivez ces étapes pour configurer et exécuter l'Iris localement : 

1.  **Cloner le dépôt** :
    ```bash
    git clone https://github.com/zephyroff/iris.git
    cd iris
    ```

2.  **Créer un environnement virtuel** (recommandé) :
    Assurez-vous d'avoir Python 3.8+ installé.
    ```bash
    python -m venv venv
    ```

3.  **Activer l'environnement virtuel** :
    *   **Windows** :
        ```bash
        .\venv\Scripts\activate
        ```
    *   **macOS/Linux** :
        ```bash
        source venv/bin/activate
        ```

4.  **Installer les dépendances** :
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

L'application utilise un fichier `settings.yaml` pour la configuration. Vous pouvez modifier ce fichier pour l'adapter à votre environnement.

**Structure du fichier `settings.yaml` :**

```yaml
server:
  host: 127.0.0.1 # Adresse IP sur laquelle le serveur écoutera
  port: 5000      # Port sur lequel le serveur écoutera

  template_dir: templates # Répertoire des modèles HTML
  static_dir: static      # Répertoire des fichiers statiques (CSS, JS, images)


secret_key: your_super_secret_key_here # Clé secrète pour la sécurité des sessions Flask.
                                       # CRITIQUE - Changez cette valeur en production.

app:
  mode: dev    # Mode de l'application (par exemple, 'dev' pour développement, 'prod' pour production)
  debug: False # Active/désactive le mode débogage de Flask. Définir à False en production.

  auth: True   # Active/désactive le système d'authentification
  admin: True  # Active/désactive le panneau d'administration
  home: True   # Active/désactive la page d'accueil

auto_protect:
  enable: True     # Active/désactive le système de protection automatique (Fail2Ban-like)
  blacklist: "null" # Liste noire d'adresses IP (sous forme de liste)
  whitelist: "null" # Liste blanche d'adresses IP (sous forme de liste)
  max_fail: 5      # Nombre maximal d'échecs avant bannissement
  fail_interval: 300 # Intervalle de temps (en secondes) pour compter les échecs
  ban_time: 300    # Durée du bannissement (en secondes)

database:
  engine: sqlite    # Moteur de base de données (actuellement 'sqlite' supporté)
  filename: app.db  # Nom du fichier de base de données SQLite
```

## Initialisation de la Base de Données

L'application utilise SQLite. Le fichier de base de données (`instance/hub.db` par défaut) sera créé automatiquement lors de la première exécution s'il n'existe pas. Aucune étape de migration explicite n'est généralement requise pour la configuration initiale avec SQLite, car `models/database.py` gère la création des tables.

## Exécution de l'Application

Pour démarrer le serveur de développement Flask :

```bash
python app.py
```

L'application s'exécutera généralement sur `http://127.0.0.1:5000`.

## Points d'API

Les points d'API sont définis dans `views/api_views.py` et sont accessibles via le préfixe `/api/<nom_du_script>`.

Les scripts d'API sont à ajouter dans le répertoire fabric. Pour les rendre compatible avec l'application, il faudrait ajouter le decorateur interne pour définir le point d'entrée de l'API/
Par exemple:

```python
from core.decorator import entrypoint

@entrypoint
def saluer(nom: str, titre: str="Monsieur/Madame"):
    """
    Retourne un message de salutation personnalisé.
    """
    return {"message": f"Bonjour {titre} {nom} !"}
```

**Authentification des API :**

Les scripts API peuvent être configurés comme `public` ou `non-public` via le panneau d'administration.

*   **Scripts Publics** : Ne nécessitent aucune authentification.
*   **Scripts Non-Publics** : Nécessitent une authentification via un jeton API valide.

Pour les scripts non-publics, les requêtes API doivent inclure un jeton dans l'en-tête `Authorization` au format `Bearer <votre_jeton_api>`.

**Types de jetons API :**

*   **Jeton d'application (`app` type)** : Ce jeton est lié à des scripts API spécifiques. Il ne peut accéder qu'aux scripts pour lesquels il a été explicitement autorisé via le panneau d'administration.
*   **Jeton universel (`universal` type)** : Ce jeton a accès à tous les scripts API non-publics.

**Exemple d'en-tête d'authentification :**
```
Authorization: Bearer VOTRE_JETON_API_ICI
```

**Exemple de point d'API : `/api/salutation`**

*   **GET /api/salutation** : Renvoie un message de salutation.
    *   **Réponse** : `{"message": "Bonjour depuis Iris !"}`

*   **POST /api/salutation** : Accepte un nom et renvoie une salutation personnalisée.
    *   **Corps de la requête (JSON)** :
        ```json
        {
            "name": "John Doe"
        }
        ```
    *   **Réponse** : `{"message": "Bonjour, John Doe !"}`

*(Une documentation API plus détaillée serait généralement générée ou fournie séparément pour une API de production.)*

## Panneau d'Administration

Le panneau d'administration fournit une interface web pour gérer l'application. Il est accessible à l'adresse `/admin` et nécessite une connexion utilisateur.

**Identifiants par défaut (à modifier via le panneau d'administration après la première connexion) :**
*   Nom d'utilisateur : `admin`
*   Mot de passe : `password`

**Fonctionnalités clés de l'administration :**
*   **Tableau de bord** : Aperçu de l'état du système.
*   **Gestion des utilisateurs** : Créer, modifier et supprimer des comptes utilisateurs.
*   **Gestion des jetons API** : Générer, révoquer et gérer les jetons API pour les utilisateurs.
*   **Gestion des scripts API** : Activer/désactiver des scripts, définir leur visibilité (public/non-public).
*   **Visionneuse de journaux** : Consulter divers journaux d'application (API, système, web, socket).
*   **Gestion des adresses IP bannies** : Consulter et gérer les adresses IP bannies par le système `auto_protect`.

## Structure du Projet

*   `app.py` : Le point d'entrée principal de l'application Flask.
*   `requirements.txt` : Liste toutes les dépendances Python.
*   `settings.yaml` : Fichier de configuration de l'application.
*   `test_api.py` : Exemple de fichier de test pour l'API.
*   `core/` : Contient la logique principale de l'application telle que l'authentification, la configuration, la gestion des erreurs, la journalisation et les décorateurs.
*   `fabric/` : Contient les scripts API exécutables par le worker (par exemple, `salutation.py`, `test_worker.py`).
*   `instance/` : Stocke les données spécifiques à l'instance, y compris la base de données SQLite (`hub.db`).
*   `models/` : Définit les modèles de base de données et les interactions (`database.py`).
*   `static/` : Actifs statiques comme les CSS, JavaScript et les images.
*   `templates/` : Modèles HTML pour le rendu des pages web, y compris les modèles du panneau d'administration.
*   `views/` : Définit les blueprints et les routes Flask pour différentes parties de l'application (par exemple, `api_views.py` pour l'API, `admin_views.py` pour le panneau d'administration, `views.py` pour les pages web générales).
