
# nsm_cli.py
# MVP (Produit Minimum Viable) pour Nexus Simple Memory
# Version 2.0 avec Recherche Sémantique
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
import pickle
from pathlib import Path
import datetime

# --- Dépendances pour la recherche sémantique ---
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    SEMANTIC_ENABLED = True
except ImportError:
    SEMANTIC_ENABLED = False

# --- Constantes ---
SEMANTIC_MODEL_NAME = 'all-MiniLM-L6-v2'
VECTOR_DIMENSION = 384

def db_connect(db_path):
    con = sqlite3.connect(db_path, check_same_thread=False)
    con.execute("PRAGMA foreign_keys = ON;")
    return con

def nsm_init(db_path):
    if Path(db_path).exists():
        print(f"Erreur: Le fichier d'archive '{db_path}' existe déjà.")
        return

    print(f"Initialisation d'une nouvelle archive NSM : {db_path}")
    with db_connect(db_path) as con:
        con.executescript('''
            CREATE TABLE files (
                id INTEGER PRIMARY KEY,
                path TEXT NOT NULL UNIQUE,
                original_size INTEGER NOT NULL,
                compressed_size INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                content BLOB
            );
            CREATE VIRTUAL TABLE files_fts USING fts5(
                path, content, content='files', content_rowid='id'
            );
            CREATE TABLE semantic_index (
                file_id INTEGER PRIMARY KEY,
                vector BLOB NOT NULL,
                FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE
            );
            CREATE TRIGGER files_after_insert AFTER INSERT ON files BEGIN
                INSERT INTO files_fts(rowid, path, content) VALUES (new.id, new.path, new.content);
            END;
            CREATE TRIGGER files_before_delete BEFORE DELETE ON files BEGIN
                DELETE FROM files_fts WHERE rowid=old.id;
                DELETE FROM semantic_index WHERE file_id=old.id;
            END;
            CREATE TRIGGER files_before_update BEFORE UPDATE ON files BEGIN
                DELETE FROM files_fts WHERE rowid=old.id;
                INSERT INTO files_fts(rowid, path, content) VALUES (new.id, new.path, new.content);
            END;
        ''')
    print("Archive initialisée avec succès.")

def is_text_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except (UnicodeDecodeError, IOError):
        return False

def nsm_add(db_path, target_path_str):
    if not Path(db_path).exists():
        return print(f"Erreur: Archive '{db_path}' non trouvée. Utilisez 'init' pour la créer.")
    
    target_path = Path(target_path_str).resolve()
    if not target_path.exists():
        return print(f"Erreur: Le chemin '{target_path_str}' n'existe pas.")

    model = SentenceTransformer(SEMANTIC_MODEL_NAME) if SEMANTIC_ENABLED else None
    if model: print("Modèle sémantique chargé.")

    zstd_compressor = zstandard.ZstdCompressor()
    files_to_process = [target_path] if target_path.is_file() else [p for p in target_path.rglob('*') if p.is_file()]

    with db_connect(db_path) as con:
        for file_path in files_to_process:
            try:
                archive_path = str(file_path.relative_to(target_path.parent))
                print(f"Traitement : {archive_path}")

                original_content = file_path.read_bytes()
                is_text = is_text_file(file_path)
                fts_content = original_content.decode('utf-8', errors='ignore') if is_text else ''
                
                cur = con.cursor()
                cur.execute('''
                    INSERT INTO files (path, original_size, compressed_size, created_at, content)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(path) DO UPDATE SET
                        original_size=excluded.original_size, compressed_size=excluded.compressed_size,
                        created_at=excluded.created_at, content=excluded.content
                ''', (archive_path, len(original_content), len(zstd_compressor.compress(original_content)),
                      datetime.datetime.now().isoformat(), zstd_compressor.compress(original_content)))
                
                file_id = cur.execute('SELECT id FROM files WHERE path = ?', (archive_path,)).fetchone()[0]
                cur.execute('INSERT INTO files_fts (rowid, path, content) VALUES (?, ?, ?) ON CONFLICT(rowid) DO UPDATE SET content=excluded.content', (file_id, archive_path, fts_content))
                
                if model and is_text and fts_content:
                    vector = model.encode(fts_content, convert_to_numpy=True)
                    cur.execute('INSERT INTO semantic_index (file_id, vector) VALUES (?, ?) ON CONFLICT(file_id) DO UPDATE SET vector=excluded.vector', (file_id, pickle.dumps(vector)))
                con.commit()
            except Exception as e:
                print(f"  -> Erreur pour {file_path}: {e}")
    print("\nOpération d'ajout terminée.")

def nsm_list(db_path):
    with db_connect(db_path) as con:
        rows = con.execute("SELECT path, original_size, compressed_size, created_at FROM files ORDER BY path").fetchall()
        if not rows: return print("L'archive est vide.")
        
        print(f"{'Chemin':<50} {'Taille Origine':>15} {'Taille Compressée':>20} {'Ratio':>8} {'Date Ajout':>25}")
        print("-" * 120)
        total_orig, total_comp = sum(r[1] for r in rows), sum(r[2] for r in rows)
        for path, original, compressed, created_at in rows:
            ratio = f"{(compressed / original * 100):.2f}%" if original > 0 else "N/A"
            print(f"{path:<50} {original:>15,}o {compressed:>20,}o {ratio:>8} {created_at:<25}")
        
        print("-" * 120)
        total_ratio = f"{(total_comp / total_orig * 100):.2f}%" if total_orig > 0 else "N/A"
        print(f"{'TOTAL':<50} {total_orig:>15,}o {total_comp:>20,}o {total_ratio:>8}")

def nsm_search(db_path, query):
    with db_connect(db_path) as con:
        results = con.execute("SELECT path, snippet(files_fts, 2, '->', '<-', '...', 20) FROM files_fts WHERE files_fts MATCH ? ORDER BY rank", (query,)).fetchall()
        if not results: return print(f"Aucun résultat pour '{query}'.")
        print(f"Résultats de recherche pour '{query}':\n")
        for path, matched_text in results:
            print(f"📄 Fichier: {path}\n   Extrait: ...{matched_text.replace(chr(10), ' ')}...\n" + "-"*20)

def nsm_search_semantic(db_path, query, top_k=5):
    if not SEMANTIC_ENABLED: return print("Recherche sémantique non disponible (dépendances manquantes).")
    
    with db_connect(db_path) as con:
        db_data = con.execute("SELECT file_id, vector FROM semantic_index").fetchall()
        if not db_data: return print("Aucun contenu sémantique à rechercher.")
        
        file_ids = np.array([item[0] for item in db_data])
        vectors = np.array([pickle.loads(item[1]) for item in db_data])

    index = faiss.IndexFlatL2(VECTOR_DIMENSION)
    index.add(vectors)
    model = SentenceTransformer(SEMANTIC_MODEL_NAME)
    query_vector = model.encode([query], convert_to_numpy=True)
    distances, indices = index.search(query_vector, min(top_k, len(file_ids)))
    
    with db_connect(db_path) as con:
        print(f"\nRésultats de recherche sémantique pour '{query}':\n")
        for i, file_idx in enumerate(indices[0]):
            file_id = file_ids[file_idx]
            path = con.execute("SELECT path FROM files WHERE id = ?", (int(file_id),)).fetchone()[0]
            print(f"#{i+1}: {path} (Similarité: {(1-distances[0][i]):.2%})")

def nsm_extract(db_path, output_dir_str, file_to_extract=None):
    output_dir = Path(output_dir_str)
    output_dir.mkdir(parents=True, exist_ok=True)
    decompressor = zstandard.ZstdDecompressor()
    with db_connect(db_path) as con:
        sql = "SELECT path, content FROM files" + (" WHERE path = ?" if file_to_extract else "")
        params = (file_to_extract,) if file_to_extract else ()
        rows = con.execute(sql, params).fetchall()
        if not rows: return print("Aucun fichier à extraire.")

        for path_str, compressed_content in rows:
            dest_path = output_dir / path_str
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(decompressor.decompress(compressed_content))
            print(f"  -> Extrait : {dest_path}")
    print("\nExtraction terminée.")

def main():
    parser = argparse.ArgumentParser(description="Nexus Simple Memory (NSM)", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('db', help="Chemin vers le fichier d'archive .nsm")
    subparsers = parser.add_subparsers(dest='command', required=True)

    subparsers.add_parser('init', help="Crée une archive .nsm vide.")
    p_add = subparsers.add_parser('add', help="Ajoute un fichier/dossier à l'archive.")
    p_add.add_argument('path', help="Chemin du fichier/dossier.")
    subparsers.add_parser('list', help="Liste le contenu de l'archive.")
    p_search = subparsers.add_parser('search', help="Recherche par mot-clé.")
    p_search.add_argument('query', help="Texte à rechercher.")
    
    if SEMANTIC_ENABLED:
        p_ssearch = subparsers.add_parser('search-semantic', help="Recherche par similarité de sens.")
        p_ssearch.add_argument('query', help="Phrase pour la recherche.")
        p_ssearch.add_argument('-k', type=int, default=5, help="Nombre de résultats.")
    
    p_extract = subparsers.add_parser('extract', help="Extrait des fichiers.")
    p_extract.add_argument('output_dir', help="Dossier de destination.")
    p_extract.add_argument('--file', required=False, help="Fichier spécifique à extraire.")

    args = parser.parse_args()
    actions = {
        'init': lambda: nsm_init(args.db),
        'add': lambda: nsm_add(args.db, args.path),
        'list': lambda: nsm_list(args.db),
        'search': lambda: nsm_search(args.db, args.query),
        'extract': lambda: nsm_extract(args.db, args.output_dir, args.file),
        'search-semantic': lambda: nsm_search_semantic(args.db, args.query, args.k) if SEMANTIC_ENABLED else None
    }
    if args.command in actions:
        actions[args.command]()

if __name__ == '__main__':
    if not SEMANTIC_ENABLED:
        print("Avertissement: Les dépendances pour la recherche sémantique sont manquantes.")
        print("Veuillez installer 'sentence-transformers' et 'faiss-cpu' pour activer cette fonctionnalité.")
    main()
