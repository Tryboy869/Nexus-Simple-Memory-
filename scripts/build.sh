#!/bin/bash

# build.sh - Script de build multi-plateforme pour NSM
#
# Ce script compile l'application NSM pour Linux, Windows et macOS,
# génère des checksums SHA-256 et package les binaires dans des archives.

set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
APP_NAME="nsm"
OUTPUT_DIR="./bin"
MAIN_PACKAGE="github.com/nexus/nsm/cmd/nsm"

# --- Versioning ---
# Essayez d'obtenir la version depuis la dernière étiquette Git. Sinon, utilisez 'dev'.
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "dev")
COMMIT_HASH=$(git rev-parse --short HEAD)
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

# LDFLAGS injecte les informations de version dans le binaire au moment de la compilation.
LDFLAGS="-s -w -X main.Version=${VERSION} -X main.Commit=${COMMIT_HASH} -X main.BuildDate=${BUILD_DATE}"

# --- Plateformes cibles ---
# Format: GOOS/GOARCH/Extension
PLATFORMS="linux/amd64/ \
           windows/amd64/.exe \
           darwin/amd64/ \
           darwin/arm64/" # Pour les Mac Apple Silicon

# --- Nettoyage et Préparation ---
echo "--- Nettoyage du répertoire de sortie ---"
rm -rf "${OUTPUT_DIR}"
mkdir -p "${OUTPUT_DIR}"

# --- Compilation ---
echo "--- Démarrage de la compilation pour la version ${VERSION} ---"

for platform in ${PLATFORMS}; do
    # Divise la chaîne de la plateforme en GOOS, GOARCH, et l'extension du binaire.
    IFS='/' read -r GOOS GOARCH EXT <<< "${platform}"
    
    OUTPUT_NAME="${APP_NAME}-${GOOS}-${GOARCH}${EXT}"
    OUTPUT_PATH="${OUTPUT_DIR}/${OUTPUT_NAME}"
    
    echo "Compiling for ${GOOS}/${GOARCH}..."
    
    # Exécute la commande de compilation Go avec les variables d'environnement appropriées.
    env GOOS=${GOOS} GOARCH=${GOARCH} go build -ldflags="${LDFLAGS}" -o "${OUTPUT_PATH}" "${MAIN_PACKAGE}"
    
    if [ $? -ne 0 ]; then
        echo "La compilation pour ${GOOS}/${GOARCH} a échoué."
        exit 1
    fi
done

echo "--- Compilation terminée ---"

# --- Packaging et Checksums ---
echo "--- Génération des archives et des checksums ---"
cd "${OUTPUT_DIR}"

for f in *; do
    # Ne pas archiver les archives elles-mêmes
    if [[ "$f" == *.tar.gz || "$f" == *.zip || "$f" == *.sha256 ]]; then
        continue
    fi
    
    echo "Packaging ${f}..."
    if [[ "$f" == *.exe ]]; then
        zip "${f}.zip" "${f}"
    else
        tar -czf "${f}.tar.gz" "${f}"
    fi
done

# Générer les checksums pour toutes les archives.
sha256sum *.zip *.tar.gz > "${APP_NAME}_${VERSION}_checksums.sha256"

cd ..
echo "--- Build terminé avec succès ! ---"
echo "Les binaires sont disponibles dans le répertoire ${OUTPUT_DIR}."

# --- Support Docker (Optionnel) ---
read -p "Voulez-vous construire une image Docker ? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "--- Construction de l'image Docker ---"
    docker build -t "${APP_NAME}:${VERSION}" .
    echo "Image Docker ${APP_NAME}:${VERSION} construite."
fi
