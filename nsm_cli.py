# nsm_cli.py
# MVP (Produit Minimum Viable) pour Nexus Simple Memory
# Version 2 avec Recherche Sémantique
#
# Dépendances :
# pip install zstandard sentence-transformers faiss-cpu numpy
#
# Auteur: Inspiré par votre idée et codé par Gemini
# Date: 27/06/2025

import sqlite3
import zstandard
import argparse
import os
import numpy as np
import pickle # Pour sérialiser les vecteurs numpy
from pathlib import Path
import datetime

# --- Dépendances pour la recherche sémantique ---
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    SEMANTIC_ENABLED = True
except ImportError:
    SEMANTIC_ENABLED = False
    print("Avertissement : Les bibliothèques pour la recherche sémantique (sentence-transformers, faiss-cpu) ne sont pas installées. La commande 'search-semantic' ne sera pas disponible.")
    print("Pour l'activer, lancez : pip install sentence-transformers faiss-cpu numpy")


# --- Constantes ---
SEMANTIC_MODEL_NAME = 'all-MiniLM-L6-v2'
VECTOR_DIMENSION = 384


# --- Fonctions de base pour la base de données ---

def db_connect(db_path):
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON;")
    return con

def nsm_init(db_path):
    if Path(db_path).exists():
        print(f"Erreur : Le fichier d'archive '{db_path}' existe déjà.")
        return

    print(f"Initialisation d'une nouvelle archive NSM à : {db_path}")
    with db_connect(db_path) as con:
        cur = con.cursor()
        cur.execute('''
            CREATE TABLE files (
                id INTEGER PRIMARY KEY,
                path TEXT NOT NULL UNIQUE,
                original_size INTEGER NOT NULL,
                compressed_size INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                content BLOB
            )
        ''')
        cur.execute('''
            CREATE VIRTUAL TABLE files_fts USING fts5(
                path,
                content,
                content='files',
                content_rowid='id'
            )
        ''')
        cur.execute('''
            CREATE TABLE semantic_index (
                file_id INTEGER PRIMARY KEY,
                vector BLOB NOT NULL,
                FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
            )
        ''')
        cur.executescript('''
            CREATE TRIGGER files_after_insert AFTER INSERT ON files
            BEGIN
                INSERT INTO files_fts(rowid, path, content)
                VALUES (new.id, new.path, new.content);
            END;

            CREATE TRIGGER files_before_delete BEFORE DELETE ON files
            BEGIN
                DELETE FROM files_fts WHERE rowid=old.id;
                DELETE FROM semantic_index WHERE file_id=old.id;
            END;

            CREATE TRIGGER files_before_update BEFORE UPDATE ON files
            BEGIN
                DELETE FROM files_fts WHERE rowid=old.id;
                INSERT INTO files_fts(rowid, path, content)
                VALUES (new.id, new.path, new.content);
            END;
        ''')
        con.commit()
    print("Archive initialisée avec succès.")


# --- Fonctions pour les opérations sur l'archive ---

def is_text_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except (UnicodeDecodeError, IOError):
        return False

def nsm_add(db_path, target_path_str):
    if not Path(db_path).exists():
        print(f"Erreur : L'archive '{db_path}' n'existe pas. Utilisez 'init' pour la créer.")
        return
    
    target_path = Path(target_path_str).resolve()
    if not target_path.exists():
        print(f"Erreur : Le chemin '{target_path_str}' n'existe pas.")
        return

    model = None
    if SEMANTIC_ENABLED:
        print("Chargement du modèle sémantique...")
        model = SentenceTransformer(SEMANTIC_MODEL_NAME)
        print("Modèle chargé.")

    zstd_compressor = zstandard.ZstdCompressor()

    files_to_process = []
    if target_path.is_file():
        files_to_process.append(target_path)
    elif target_path.is_dir():
        files_to_process.extend(p for p in target_path.rglob('*') if p.is_file())

    with db_connect(db_path) as con:
        cur = con.cursor()
        for file_path in files_to_process:
            try:
                archive_path = str(file_path.relative_to(target_path.parent))
                print(f"Traitement de : {archive_path}")

                original_content = file_path.read_bytes()
                original_size = len(original_content)
                compressed_content = zstd_compressor.compress(original_content)
                compressed_size = len(compressed_content)
                
                is_text = is_text_file(file_path)
                fts_content = original_content.decode('utf-8', errors='ignore') if is_text else ''
                
                cur.execute('''
                    INSERT INTO files (path, original_size, compressed_size, created_at, content)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(path) DO UPDATE SET
                        original_size=excluded.original_size,
                        compressed_size=excluded.compressed_size,
                        created_at=excluded.created_at,
                        content=excluded.content
                ''', (archive_path, original_size, compressed_size, datetime.datetime.now().isoformat(), compressed_content))
                
                last_id_query = cur.execute('SELECT id FROM files WHERE path = ?', (archive_path,))
                last_id = last_id_query.fetchone()[0]

                cur.execute('''
                    INSERT INTO files_fts (rowid, path, content) VALUES (?, ?, ?)
                    ON CONFLICT(rowid) DO UPDATE SET path=excluded.path, content=excluded.content
                ''', (last_id, archive_path, fts_content))
                
                if model and is_text and fts_content:
                    vector = model.encode(fts_content, convert_to_numpy=True)
                    vector_blob = pickle.dumps(vector)
                    cur.execute('''
                        INSERT INTO semantic_index (file_id, vector) VALUES (?, ?)
                        ON CONFLICT(file_id) DO UPDATE SET vector=excluded.vector
                    ''', (last_id, vector_blob))

            except Exception as e:
                print(f"  -> Erreur lors de l'ajout de {file_path}: {e}")
        con.commit()
    print("\nOpération d'ajout terminée.")


def nsm_list(db_path):
    if not Path(db_path).exists(): return print(f"Erreur: Archive '{db_path}' non trouvée.")
    with db_connect(db_path) as con:
        rows = con.cursor().execute("SELECT path, original_size, compressed_size, created_at FROM files ORDER BY path").fetchall()
        if not rows: return print("L'archive est vide.")
        
        print(f"{'Chemin dans l'archive':<50} {'Taille Origine':>15} {'Taille Compressée':>20} {'Ratio':>8} {'Date Ajout':>25}")
        print("-" * 120)
        total_orig, total_comp = 0, 0
        for path, original, compressed, created_at in rows:
            total_orig += original
            total_comp += compressed
            ratio = f"{(compressed / original * 100):.2f}%" if original > 0 else "N/A"
            print(f"{path:<50} {original:>15,}o {compressed:>20,}o {ratio:>8} {created_at:<25}")
        
        print("-" * 120)
        total_ratio = f"{(total_comp / total_orig * 100):.2f}%" if total_orig > 0 else "N/A"
        print(f"{'TOTAL':<50} {total_orig:>15,}o {total_comp:>20,}o {total_ratio:>8}")


def nsm_search(db_path, query):
    if not Path(db_path).exists(): return print(f"Erreur: Archive '{db_path}' non trouvée.")
    with db_connect(db_path) as con:
        results = con.cursor().execute('''
            SELECT path, snippet(files_fts, 2, '->', '<-', '...', 20)
            FROM files_fts WHERE files_fts MATCH ? ORDER BY rank
        ''', (query,)).fetchall()

        if not results: return print(f"Aucun résultat trouvé pour '{query}'.")
        print(f"Résultats de la recherche par mot-clé pour '{query}':\n")
        for path, matched_text in results:
            print(f"📄 Fichier : {path}\n   Extrait : ...{matched_text.replace(chr(10), ' ')}...\n" + "-"*20)


def nsm_search_semantic(db_path, query, top_k=5):
    if not SEMANTIC_ENABLED: return print("Recherche sémantique non disponible.")
    if not Path(db_path).exists(): return print(f"Erreur: Archive '{db_path}' non trouvée.")
    
    print("Chargement des données pour la recherche sémantique...")
    with db_connect(db_path) as con:
        db_data = con.cursor().execute("SELECT file_id, vector FROM semantic_index").fetchall()
        if not db_data: return print("Aucun contenu sémantique à rechercher dans l'archive.")
        
        file_ids = np.array([item[0] for item in db_data])
        vectors = np.array([pickle.loads(item[1]) for item in db_data])

    print("Création de l'index de recherche (FAISS)...")
    index = faiss.IndexFlatL2(VECTOR_DIMENSION)
    index.add(vectors)

    print("Génération du vecteur pour la requête...")
    model = SentenceTransformer(SEMANTIC_MODEL_NAME)
    query_vector = model.encode([query], convert_to_numpy=True)

    print(f"Recherche des {top_k} plus proches voisins...")
    distances, indices = index.search(query_vector, top_k)
    
    results_ids = file_ids[indices[0]]
    
    with db_connect(db_path) as con:
        print(f"\nRésultats de la recherche sémantique pour '{query}':\n")
        for i, file_id in enumerate(results_ids):
            path = con.cursor().execute("SELECT path FROM files WHERE id = ?", (int(file_id),)).fetchone()[0]
            print(f"#{i+1} - Fichier : {path} (Distance: {distances[0][i]:.2f})")


def nsm_extract(db_path, output_dir_str, file_to_extract=None):
    if not Path(db_path).exists(): return print(f"Erreur: Archive '{db_path}' non trouvée.")
    output_dir = Path(output_dir_str)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Extraction vers : {output_dir.resolve()}")
    
    zstd_decompressor = zstandard.ZstdDecompressor()
    with db_connect(db_path) as con:
        query = "SELECT path, content FROM files"
        params = [file_to_extract] if file_to_extract else []
        if file_to_extract: query += " WHERE path = ?"
        
        rows = con.cursor().execute(query, params).fetchall()
        if not rows: return print(f"Aucun fichier à extraire.")

        for path_str, compressed_content in rows:
            dest_path = output_dir / path_str
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(zstd_decompressor.decompress(compressed_content))
            print(f"  -> Extrait : {dest_path}")
    print("\nExtraction terminée.")


def main():
    parser = argparse.ArgumentParser(description="Nexus Simple Memory (NSM)", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('db', help="Chemin vers le fichier d'archive .nsm")
    subparsers = parser.add_subparsers(dest='command', required=True, help="Commandes")

    subparsers.add_parser('init', help="Crée une archive .nsm vide.")
    parser_add = subparsers.add_parser('add', help="Ajoute un fichier/dossier à l'archive.")
    parser_add.add_argument('path', help="Chemin du fichier/dossier à ajouter.")
    subparsers.add_parser('list', help="Liste le contenu de l'archive.")
    parser_search = subparsers.add_parser('search', help="Recherche par mot-clé (rapide).")
    parser_search.add_argument('query', help="Texte à rechercher.")
    
    if SEMANTIC_ENABLED:
        parser_ssearch = subparsers.add_parser('search-semantic', help="Recherche par similarité de sens (plus lent).")
        parser_ssearch.add_argument('query', help="Phrase ou question pour la recherche sémantique.")
        parser_ssearch.add_argument('-k', '--top_k', type=int, default=5, help="Nombre de résultats à afficher.")

    parser_extract = subparsers.add_parser('extract', help="Extrait des fichiers de l'archive.")
    parser_extract.add_argument('output_dir', help="Dossier de destination.")
    parser_extract.add_argument('--file', help="Optionnel: fichier spécifique à extraire.", required=False)

    args = parser.parse_args()

    if args.command == 'init': nsm_init(args.db)
    elif args.command == 'add': nsm_add(args.db, args.path)
    elif args.command == 'list': nsm_list(args.db)
    elif args.command == 'search': nsm_search(args.db, args.query)
    elif args.command == 'extract': nsm_extract(args.db, args.output_dir, args.file)
    elif args.command == 'search-semantic' and SEMANTIC_ENABLED:
        nsm_search_semantic(args.db, args.query, args.top_k)

if __name__ == '__main__':
    main()