# Nexus Simple Memory (NSM)

Ce dépôt contient le code pour le Produit Minimum Viable (MVP) de Nexus Simple Memory, un outil de stockage compressé, intelligent et auto-indexé.

## 🎯 Objectif

Transformer n'importe quel ensemble de fichiers en une archive `.nsm` unique, compacte et interrogeable, en local, sans dépendre d'un service cloud.

## ⚙️ Fonctionnalités du MVP

* **Création d'archive** : `nsm_cli.py <archive.nsm> init`
* **Ajout de données** : `nsm_cli.py <archive.nsm> add <chemin/vers/dossier/ou/fichier>`
* **Liste du contenu** : `nsm_cli.py <archive.nsm> list`
* **Extraction de données** : `nsm_cli.py <archive.nsm> extract <dossier_de_sortie>`
* **Recherche par mot-clé** : `nsm_cli.py <archive.nsm> search "mon mot"`
* **Recherche sémantique (par sens)** : `nsm_cli.py <archive.nsm> search-semantic "une phrase qui décrit ce que je cherche"`

## 🚀 Installation

1.  Clonez ce dépôt :
    ```bash
    git clone [https://github.com/](https://github.com/)Tryboy869/Nexus-Simple-Memory-.git
    cd Nexus-Simple-Memory-
    ```

2.  (Optionnel mais recommandé) Créez un environnement virtuel :
    ```bash
    python -m venv venv
    source venv/bin/activate  # Sur Linux/macOS
    # .\venv\Scripts\activate # Sur Windows
    ```

3.  Installez les dépendances :
    ```bash
    pip install -r requirements.txt
    ```

## 📝 Exemples d'utilisation

```bash
# 1. Créer une nouvelle archive
python nsm_cli.py ma_base.nsm init

# 2. Ajouter un dossier de projet
python nsm_cli.py ma_base.nsm add ./mon_code_source

# 3. Lister les fichiers archivés
python nsm_cli.py ma_base.nsm list

# 4. Rechercher tous les fichiers parlant de "base de données"
python nsm_cli.py ma_base.nsm search "base de données"

# 5. Rechercher des fichiers similaires à l'idée "comment optimiser les requêtes"
python nsm_cli.py ma_base.nsm search-semantic "comment optimiser les requêtes sql"
```