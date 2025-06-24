# 🚀 NSM - Nexus Simple Memory

**Stockage compressé intelligent avec recherche sémantique**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

NSM transforme la façon dont vous stockez et recherchez vos données en combinant compression avancée et intelligence artificielle.

## ✨ Fonctionnalités

- 🔒 **Système de tokens sécurisé** - Protection et gestion des accès
- 📦 **Compression multi-algorithmes** - LZMA, Brotli, Zstandard avec sélection automatique
- 🔍 **Recherche sémantique** - Trouvez le contenu par sens, pas seulement par mots-clés  
- 💾 **Format binaire optimisé** - Stockage efficace avec métadonnées
- 🚀 **CLI et API Python** - Interface en ligne de commande et intégration programmatique
- 📊 **Statistiques détaillées** - Suivi des performances de compression

## 🛠️ Installation

```bash
# Installation standard
pip install nsm

# Installation avec support GPU (optionnel)
pip install nsm[gpu]

# Installation pour développement
pip install nsm[dev]
```

## 🚀 Utilisation rapide

### Interface CLI

```bash
# Compresser un fichier
nsm compress document.txt --license YOUR_LICENSE_KEY

# Rechercher dans un fichier NSM
nsm search document.nsm "intelligence artificielle"

# Extraire le contenu
nsm extract document.nsm -o extracted_folder

# Informations sur un fichier NSM
nsm info document.nsm
```

### API Python

```python
from nsm import NSMEncoder, NSMRetriever

# 📦 Encoder des données
encoder = NSMEncoder(license_key="your_32_char_license_key")
encoder.add_text("Votre contenu textuel", source="document.txt")
encoder.add_directory("./mes_documents")
encoder.build_nsm("ma_base.nsm")

# 🔍 Rechercher
retriever = NSMRetriever("ma_base.nsm")
results = retriever.search("recherche sémantique", top_k=5)

for chunk, score in results:
    print(f"Score: {score:.3f}")
    print(f"Contenu: {chunk[:100]}...")
```

## 📋 Exemples d'usage

### Archivage intelligent de documents
```bash
# Compresser une bibliothèque de documents
nsm compress ./bibliotheque --license YOUR_KEY -o bibliotheque.nsm

# Rechercher dans tous les documents
nsm search bibliotheque.nsm "machine learning applications"
```

### Analyse de logs
```python
from nsm import NSMEncoder, NSMRetriever

# Compresser des logs
encoder = NSMEncoder(license_key="your_key")
encoder.add_directory("./logs")
encoder.build_nsm("logs_compressed.nsm")

# Rechercher des erreurs spécifiques
retriever = NSMRetriever("logs_compressed.nsm")
errors = retriever.search("connection timeout error", top_k=10)
```

## 🔧 Configuration avancée

### Variables d'environnement
```bash
export NSM_LICENSE_KEY="your_license_key"
export NSM_COMPRESSION_LEVEL=6
export NSM_SEARCH_THRESHOLD=0.7
```

### Utilisation programmatique avancée
```python
from nsm import NSMCompressor, NSMFormat

# Compression personnalisée
compressor = NSMCompressor()
compressed_data, algo, ratio = compressor.auto_compress(data)

# Manipulation de format
nsm_format = NSMFormat()
data, index, metadata = nsm_format.read_nsm_file("file.nsm")
```

## 📈 Performance

| Algorithme | Vitesse | Compression | Usage recommandé |
|------------|---------|-------------|------------------|
| Zstandard  | ⚡⚡⚡   | ⭐⭐       | Données temps réel |
| Brotli     | ⚡⚡     | ⭐⭐⭐     | Web, texte |
| LZMA       | ⚡       | ⭐⭐⭐⭐   | Archivage long terme |

## 🔒 Sécurité et Licences

NSM utilise un système de tokens pour contrôler l'accès et l'usage:
- Clés de licence de 32 caractères alphanumériques
- Tokens de session temporaires
- Chiffrement des métadonnées sensibles

## 🤝 Contribution

Les contributions sont bienvenues ! Consultez notre guide de contribution.

## 📄 Licence

MIT License - voir le fichier LICENSE pour plus de détails.

## 🆘 Support

- 📧 Issues: [GitHub Issues](https://github.com/Tryboy869/Nexus-Simple-Memory-/issues)
- 📖 Documentation: [Wiki](https://github.com/Tryboy869/Nexus-Simple-Memory-/wiki)
- 💬 Discussions: [GitHub Discussions](https://github.com/Tryboy869/Nexus-Simple-Memory-/discussions)

---

Fait avec ❤️ par l'équipe NSM
