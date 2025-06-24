import lzma
import brotli
import zstandard as zstd
from typing import Tuple, Optional
import logging

class NSMCompressor:
    def __init__(self):
        self.algorithms = {
            'lzma': self._compress_lzma,
            'brotli': self._compress_brotli,
            'zstd': self._compress_zstd
        }
        
    def auto_compress(self, data: bytes) -> Tuple[bytes, str, float]:
        """Compression automatique avec le meilleur algorithme"""
        if not data:
            return data, 'none', 1.0
            
        best_ratio = float('inf')
        best_compressed = data
        best_algo = 'none'
        original_size = len(data)
        
        for name, compressor in self.algorithms.items():
            try:
                compressed = compressor(data)
                ratio = len(compressed) / original_size
                
                if ratio < best_ratio:
                    best_ratio = ratio
                    best_compressed = compressed
                    best_algo = name
                    
            except Exception as e:
                logging.warning(f"Erreur compression {name}: {e}")
                continue
                
        return best_compressed, best_algo, best_ratio
    
    def decompress(self, data: bytes, algorithm: str) -> bytes:
        """Décompression selon l'algorithme spécifié"""
        try:
            if algorithm == 'lzma':
                return lzma.decompress(data)
            elif algorithm == 'brotli':
                return brotli.decompress(data)
            elif algorithm == 'zstd':
                dctx = zstd.ZstdDecompressor()
                return dctx.decompress(data)
            else:
                return data
        except Exception as e:
            raise ValueError(f"Erreur décompression {algorithm}: {e}")
    
    def _compress_lzma(self, data: bytes) -> bytes:
        return lzma.compress(data, preset=6, check=lzma.CHECK_CRC64)
    
    def _compress_brotli(self, data: bytes) -> bytes:
        return brotli.compress(data, quality=6, mode=brotli.MODE_TEXT)
    
    def _compress_zstd(self, data: bytes) -> bytes:
        cctx = zstd.ZstdCompressor(level=6, write_content_size=True)
        return cctx.compress(data)
