"""
NSMRetriever - Fast semantic search, QR frame extraction, and context assembly
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from functools import lru_cache
import cv2

from .utils import (
    extract_frame, decode_qr, batch_extract_and_decode,
    extract_and_decode_cached
)
from .index import IndexManager
from .config import get_default_config

logger = logging.getLogger(__name__)


class NSMRetriever:
    """Fast retrieval from QR code memorys using semantic search"""
    
    def __init__(self, memory_file: str, index_file: str, 
                 config: Optional[Dict[str, Any]] = None):
        self.memory_file = str(Path(memory_file).absolute())
        self.index_file = str(Path(index_file).absolute())
        self.config = config or get_default_config()
        
        self.index_manager = IndexManager(self.config)
        self.index_manager.load(str(Path(index_file).with_suffix('')))
        
        self._frame_cache = {}
        self._cache_size = self.config["retrieval"]["cache_size"]
        
        self._verify_memory()
        
        logger.info(f"Initialized retriever with {self.index_manager.get_stats()['total_chunks']} chunks")
    
    def _verify_memory(self):
        cap = cv2.MemoryCapture(self.memory_file)
        if not cap.isOpened():
            raise ValueError(f"Cannot open memory file: {self.memory_file}")
        
        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        
        logger.info(f"Memory has {self.total_frames} frames at {self.fps} fps")
    
    def search(self, query: str, top_k: int = 5) -> List[str]:
        start_time = time.time()
        search_results = self.index_manager.search(query, top_k)
        frame_numbers = list(set(result[2]["frame"] for result in search_results))
        decoded_frames = self._decode_frames_parallel(frame_numbers)
        results = []
        for chunk_id, distance, metadata in search_results:
            frame_num = metadata["frame"]
            if frame_num in decoded_frames:
                try:
                    chunk_data = json.loads(decoded_frames[frame_num])
                    results.append(chunk_data["text"])
                except (json.JSONDecodeError, KeyError):
                    results.append(metadata["text"])
            else:
                results.append(metadata["text"])
        elapsed = time.time() - start_time
        logger.info(f"Search completed in {elapsed:.3f}s for query: '{query[:50]}...'")
        return results
    
    def get_chunk_by_id(self, chunk_id: int) -> Optional[str]:
        metadata = self.index_manager.get_chunk_by_id(chunk_id)
        if metadata:
            frame_num = metadata["frame"]
            decoded = self._decode_single_frame(frame_num)
            if decoded:
                try:
                    chunk_data = json.loads(decoded)
                    return chunk_data["text"]
                except (json.JSONDecodeError, KeyError):
                    pass
            return metadata["text"]
        return None
    
    def _decode_single_frame(self, frame_number: int) -> Optional[str]:
        if frame_number in self._frame_cache:
            return self._frame_cache[frame_number]
        result = extract_and_decode_cached(self.memory_file, frame_number)
        if result and len(self._frame_cache) < self._cache_size:
            self._frame_cache[frame_number] = result
        return result
    
    def _decode_frames_parallel(self, frame_numbers: List[int]) -> Dict[int, str]:
        results = {}
        uncached_frames = []
        for frame_num in frame_numbers:
            if frame_num in self._frame_cache:
                results[frame_num] = self._frame_cache[frame_num]
            else:
                uncached_frames.append(frame_num)
        if not uncached_frames:
            return results
        max_workers = self.config["retrieval"]["max_workers"]
        decoded = batch_extract_and_decode(self.memory_file, uncached_frames, max_workers=max_workers)
        for frame_num, data in decoded.items():
            results[frame_num] = data
            if len(self._frame_cache) < self._cache_size:
                self._frame_cache[frame_num] = data
        return results
    
    def search_with_metadata(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        start_time = time.time()
        search_results = self.index_manager.search(query, top_k)
        frame_numbers = list(set(result[2]["frame"] for result in search_results))
        decoded_frames = self._decode_frames_parallel(frame_numbers)
        results = []
        for chunk_id, distance, metadata in search_results:
            frame_num = metadata["frame"]
            if frame_num in decoded_frames:
                try:
                    chunk_data = json.loads(decoded_frames[frame_num])
                    text = chunk_data["text"]
                except (json.JSONDecodeError, KeyError):
                    text = metadata["text"]
            else:
                text = metadata["text"]
            results.append({
                "text": text,
                "score": 1.0 / (1.0 + distance),
                "chunk_id": chunk_id,
                "frame": frame_num,
                "metadata": metadata
            })
        elapsed = time.time() - start_time
        logger.info(f"Search with metadata completed in {elapsed:.3f}s")
        return results
    
    def get_context_window(self, chunk_id: int, window_size: int = 2) -> List[str]:
        chunks = []
        for offset in range(-window_size, window_size + 1):
            target_id = chunk_id + offset
            chunk = self.get_chunk_by_id(target_id)
            if chunk:
                chunks.append(chunk)
        return chunks
    
    def prefetch_frames(self, frame_numbers: List[int]):
        to_prefetch = [f for f in frame_numbers if f not in self._frame_cache]
        if to_prefetch:
            logger.info(f"Prefetching {len(to_prefetch)} frames...")
            decoded = self._decode_frames_parallel(to_prefetch)
            logger.info(f"Prefetched {len(decoded)} frames")
    
    def clear_cache(self):
        self._frame_cache.clear()
        extract_and_decode_cached.cache_clear()
        logger.info("Cleared frame cache")
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "memory_file": self.memory_file,
            "total_frames": self.total_frames,
            "fps": self.fps,
            "cache_size": len(self._frame_cache),
            "max_cache_size": self._cache_size,
            "index_stats": self.index_manager.get_stats()
        }

    def get_all_chunks(self) -> List[str]:
        """Retourne tous les chunks stockés"""
        return getattr(self, 'chunks', [])
