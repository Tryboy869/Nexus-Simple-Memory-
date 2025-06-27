
# Nexus Simple Memory (NSM)

Ce dépôt contient le code pour le Produit Minimum Viable (MVP) de **Nexus Simple Memory**, un outil universel de stockage compressé, intelligent et ultra-léger.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)

## 🎯 Objectif du Projet

L'objectif est de remplacer le stockage lourd et dispersé par un format de fichier `.nsm` unique qui est :
- **Compressé** : Pour économiser de l'espace.
- **Portable** : Un seul fichier facile à déplacer, sauvegarder ou partager.
- **Auto-indexé** : Permet une recherche par mot-clé ultra-rapide.
- **Intelligent** : Permet une recherche sémantique (par sens) pour trouver l'information pertinente même sans les bons mots-clés.
- **Souverain** : L'utilisateur garde le contrôle total de ses données. NSM n'est pas un service cloud.

## ⚙️ Fonctionnalités du MVP

Ce script en ligne de commande (`nsm_cli.py`) supporte les opérations suivantes :

| Commande | Description |
|---|---|
| `init` | Crée une nouvelle archive `.nsm` vide. |
| `add` | Ajoute un fichier ou un dossier entier à l'archive. |
| `list` | Affiche la liste des fichiers contenus dans l'archive avec leurs stats. |
| `extract` | Extrait un ou tous les fichiers de l'archive vers un dossier. |
| `search` | Effectue une recherche par mot-clé (rapide, basée sur FTS5). |
| `search-semantic` | Effectue une recherche sémantique par similarité de sens. |

## 🚀 Guide de Démarrage Rapide

1.  **Clonez ce dépôt :**
    ```bash
    git clone [https://github.com/](https://github.com/)Tryboy869/Nexus-Simple-Memory-.git
    cd Nexus-Simple-Memory-
    ```

2.  **Installez les dépendances :**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Utilisez l'outil :**
    ```bash
    # Créez une archive pour vos projets
    python nsm_cli.py mes_projets.nsm init

    # Ajoutez un dossier
    python nsm_cli.py mes_projets.nsm add ./mon_code_source

    # Cherchez une fonction spécifique par mot-clé
    python nsm_cli.py mes_projets.nsm search "database connection"

    # Cherchez des concepts sémantiquement
    python nsm_cli.py mes_projets.nsm search-semantic "une fonction qui gère l'authentification des utilisateurs"
    ```
