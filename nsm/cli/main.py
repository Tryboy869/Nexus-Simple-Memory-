import argparse  
import os  
from pathlib import Path  
from typing import Optional  
  
def main():  
    """Point d'entrée principal de la CLI NSM"""  
    parser = argparse.ArgumentParser(  
        description='NSM - Nexus Simple Memory CLI',  
        formatter_class=argparse.RawDescriptionHelpFormatter,  
        epilog="""  
Exemples:  
  nsm compress data.txt --license YOUR_LICENSE_KEY  
  nsm search file.nsm "rechercher ceci"  
  nsm extract file.nsm -o output_folder  
  nsm info file.nsm  
        """  
    )  
      
    subparsers = parser.add_subparsers(dest='command', help='Commandes disponibles')  
      
    # Commande compress  
    compress_parser = subparsers.add_parser('compress', help='Compresser des données')  
    compress_parser.add_argument('input', help='Fichier ou dossier à compresser')  
    compress_parser.add_argument('-o', '--output', help='Fichier NSM de sortie')  
    compress_parser.add_argument('--license', required=True, help='Clé de licence NSM')  
    compress_parser.add_argument('-v', '--verbose', action='store_true', help='Mode verbeux')  
      
    # Commande search  
    search_parser = subparsers.add_parser('search', help='Rechercher dans un fichier NSM')  
    search_parser.add_argument('nsm_file', help='Fichier NSM')  
    search_parser.add_argument('query', help='Requête de recherche')  
    search_parser.add_argument('-k', '--top-k', type=int, default=5, help='Nombre de résultats')  
    search_parser.add_argument('-t', '--threshold', type=float, default=0.5, help='Seuil de pertinence')  
      
    # Commande extract  
    extract_parser = subparsers.add_parser('extract', help='Extraire des données')  
    extract_parser.add_argument('nsm_file', help='Fichier NSM')  
    extract_parser.add_argument('-o', '--output', help='Dossier de sortie')  
      
    # Commande info  
    info_parser = subparsers.add_parser('info', help='Informations sur un fichier NSM')  
    info_parser.add_argument('nsm_file', help='Fichier NSM')  
      
    args = parser.parse_args()  
      
    if args.command == 'compress':  
        compress_command(args)  
    elif args.command == 'search':  
        search_command(args)  
    elif args.command == 'extract':  
        extract_command(args)  
    elif args.command == 'info':  
        info_command(args)  
    else:  
        parser.print_help()  
  
def compress_command(args):  
    """Commande de compression"""  
    try:  
        from ..core.encoder import NSMEncoder  
          
        if args.verbose:  
            print(f"📦 Compression de: {args.input}")  
          
        encoder = NSMEncoder(license_key=args.license)  
          
        if os.path.isfile(args.input):  
            with open(args.input, 'r', encoding='utf-8') as f:  
                encoder.add_text(f.read())  
        elif os.path.isdir(args.input):  
            # Parcourir le dossier manuellement  
            for root, dirs, files in os.walk(args.input):  
                for file in files:  
                    if file.endswith(('.txt', '.md', '.py', '.json')):  
                        file_path = os.path.join(root, file)  
                        try:  
                            with open(file_path, 'r', encoding='utf-8') as f:  
                                encoder.add_text(f.read())  
                        except UnicodeDecodeError:  
                            print(f"⚠️  Ignoré (encoding): {file_path}")  
        else:  
            print(f"❌ Erreur: {args.input} n'existe pas")  
            return  
          
        output_file = args.output or f"{args.input}.nsm"  
        encoder.save(output_file)  
          
        # Statistiques  
        if os.path.isfile(args.input):  
            original_size = Path(args.input).stat().st_size  
            compressed_size = Path(output_file).stat().st_size  
            ratio = (1 - compressed_size / original_size) * 100  
            print(f"📊 Taux de compression: {ratio:.1f}%")  
          
        print(f"✅ Compression terminée: {output_file}")  
          
    except ImportError:  
        print("❌ Erreur: Module NSMEncoder non trouvé")  
    except Exception as e:  
        print(f"❌ Erreur lors de la compression: {e}")  
  
def search_command(args):  
    """Commande de recherche"""  
    try:  
        from ..core.retriever import NSMRetriever  
          
        if not os.path.exists(args.nsm_file):  
            print(f"❌ Erreur: {args.nsm_file} n'existe pas")  
            return  
          
        retriever = NSMRetriever(args.nsm_file)  
        results = retriever.search(args.query, top_k=args.top_k)  
          
        print(f"🔍 Résultats pour: '{args.query}'")  
        print("-" * 50)  
          
        for i, (chunk, score) in enumerate(results, 1):  
            if score >= args.threshold:  
                print(f"{i}. [Score: {score:.3f}]")  
                print(f"   {chunk[:200]}{'...' if len(chunk) > 200 else ''}")  
                print()  
          
        if not results:  
            print("Aucun résultat trouvé.")  
              
    except ImportError:  
        print("❌ Erreur: Module NSMRetriever non trouvé")  
    except Exception as e:  
        print(f"❌ Erreur lors de la recherche: {e}")  
  
def extract_command(args):  
    """Commande d'extraction"""  
    try:  
        from ..core.retriever import NSMRetriever  
          
        if not os.path.exists(args.nsm_file):  
            print(f"❌ Erreur: {args.nsm_file} n'existe pas")  
            return  
          
        retriever = NSMRetriever(args.nsm_file)  
        output_dir = args.output or "nsm_extracted"  
          
        # Créer le dossier de sortie  
        os.makedirs(output_dir, exist_ok=True)  
          
        # Extraire tous les chunks  
        all_chunks = retriever.get_all_chunks()  
          
        for i, chunk in enumerate(all_chunks):  
            with open(f"{output_dir}/chunk_{i:04d}.txt", 'w', encoding='utf-8') as f:  
                f.write(chunk)  
          
        print(f"✅ Extraction terminée: {output_dir} ({len(all_chunks)} fichiers)")  
          
    except ImportError:  
        print("❌ Erreur: Module NSMRetriever non trouvé")  
    except Exception as e:  
        print(f"❌ Erreur lors de l'extraction: {e}")  
  
def info_command(args):  
    """Commande d'informations"""  
    try:  
        from ..core.format import NSMFormat  
          
        if not os.path.exists(args.nsm_file):  
            print(f"❌ Erreur: {args.nsm_file} n'existe pas")  
            return  
          
        nsm_format = NSMFormat()  
        data, index, metadata = nsm_format.read_nsm_file(args.nsm_file)  
          
        print(f"📄 Informations NSM: {args.nsm_file}")  
        print("-" * 50)  
        print(f"Version: {metadata.get('nsm_version', 'Inconnue')}")  
        print(f"Créé le: {metadata.get('created_at', 'Inconnu')}")  
        print(f"Taille des données: {len(data)} bytes")  
        print(f"Nombre d'entrées: {len(index)}")  
        print(f"Algorithme de compression: {metadata.get('compression_algo', 'Inconnu')}")  
          
        if 'compression_ratio' in metadata:  
            print(f"Taux de compression: {metadata['compression_ratio']:.1%}")  
          
    except ImportError:  
        print("❌ Erreur: Module NSMFormat non trouvé")  
    except Exception as e:  
        print(f"❌ Erreur lors de la lecture des infos: {e}")  
  
if __name__ == '__main__':  
    main()
