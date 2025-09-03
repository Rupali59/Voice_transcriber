"""
Model Cache Manager for Whisper models
Provides efficient model loading and caching to avoid reloading models for each transcription
"""

import os
import threading
import time
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import gc
import torch

try:
    import whisper
except ImportError:
    whisper = None
    logging.warning("Whisper not available. Model caching will not work.")

logger = logging.getLogger(__name__)

class ModelCache:
    """Singleton model cache manager"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ModelCache, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.models: Dict[str, Any] = {}
        self.model_usage: Dict[str, Dict[str, Any]] = {}
        self.cache_config = {
            'max_models': int(os.getenv('WHISPER_MODEL_CACHE_SIZE', 3)),
            'idle_timeout': int(os.getenv('MODEL_IDLE_TIMEOUT', 1800)),  # 30 minutes
            'cleanup_interval': int(os.getenv('MODEL_CLEANUP_INTERVAL', 300)),  # 5 minutes
            'enable_gpu': os.getenv('ENABLE_GPU_ACCELERATION', 'true').lower() == 'true'
        }
        
        self._cleanup_thread = None
        self._start_cleanup_thread()
        self._initialized = True
        
        logger.info(f"ModelCache initialized with config: {self.cache_config}")
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return
            
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_models,
            daemon=True,
            name="ModelCacheCleanup"
        )
        self._cleanup_thread.start()
        logger.info("Model cache cleanup thread started")
    
    def get_model(self, model_size: str) -> Optional[Any]:
        """
        Get cached model or load if not cached
        
        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
            
        Returns:
            Whisper model instance or None if loading failed
        """
        if not whisper:
            logger.error("Whisper not available")
            return None
            
        with self._lock:
            # Check if model is already cached
            if model_size in self.models:
                self._update_usage(model_size)
                logger.info(f"Using cached model: {model_size}")
                return self.models[model_size]
            
            # Load new model
            return self._load_model(model_size)
    
    def _load_model(self, model_size: str) -> Optional[Any]:
        """
        Load a new model and add to cache
        
        Args:
            model_size: Whisper model size
            
        Returns:
            Loaded model or None if failed
        """
        try:
            # Check cache size limit
            if len(self.models) >= self.cache_config['max_models']:
                self._evict_least_used_model()
            
            logger.info(f"Loading Whisper model: {model_size}")
            start_time = time.time()
            
            # Load model with device optimization
            device = "cuda" if self.cache_config['enable_gpu'] and torch.cuda.is_available() else "cpu"
            model = whisper.load_model(model_size, device=device)
            
            load_time = time.time() - start_time
            logger.info(f"Model {model_size} loaded in {load_time:.2f}s on {device}")
            
            # Cache the model
            self.models[model_size] = model
            self._update_usage(model_size, is_new=True)
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model {model_size}: {e}")
            return None
    
    def _update_usage(self, model_size: str, is_new: bool = False):
        """Update model usage statistics"""
        now = datetime.now()
        
        if is_new:
            self.model_usage[model_size] = {
                'first_used': now,
                'last_used': now,
                'access_count': 1
            }
        else:
            if model_size in self.model_usage:
                self.model_usage[model_size]['last_used'] = now
                self.model_usage[model_size]['access_count'] += 1
            else:
                self.model_usage[model_size] = {
                    'first_used': now,
                    'last_used': now,
                    'access_count': 1
                }
    
    def _evict_least_used_model(self):
        """Evict the least recently used model from cache"""
        if not self.model_usage:
            return
            
        # Find least recently used model
        lru_model = min(
            self.model_usage.items(),
            key=lambda x: x[1]['last_used']
        )[0]
        
        logger.info(f"Evicting least used model: {lru_model}")
        self._unload_model(lru_model)
    
    def _unload_model(self, model_size: str):
        """Unload a model from memory"""
        if model_size in self.models:
            try:
                # Clear model from memory
                del self.models[model_size]
                
                # Clear usage stats
                if model_size in self.model_usage:
                    del self.model_usage[model_size]
                
                # Force garbage collection
                gc.collect()
                
                # Clear CUDA cache if using GPU
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                logger.info(f"Model {model_size} unloaded from cache")
                
            except Exception as e:
                logger.error(f"Error unloading model {model_size}: {e}")
    
    def _cleanup_models(self):
        """Background cleanup of idle models"""
        while True:
            try:
                time.sleep(self.cache_config['cleanup_interval'])
                
                with self._lock:
                    now = datetime.now()
                    idle_models = []
                    
                    for model_size, usage in self.model_usage.items():
                        idle_time = now - usage['last_used']
                        if idle_time.total_seconds() > self.cache_config['idle_timeout']:
                            idle_models.append(model_size)
                    
                    # Unload idle models
                    for model_size in idle_models:
                        logger.info(f"Cleaning up idle model: {model_size}")
                        self._unload_model(model_size)
                        
            except Exception as e:
                logger.error(f"Error in model cleanup thread: {e}")
    
    def preload_models(self, model_sizes: list):
        """
        Preload specified models into cache
        
        Args:
            model_sizes: List of model sizes to preload
        """
        logger.info(f"Preloading models: {model_sizes}")
        
        for model_size in model_sizes:
            if model_size not in self.models:
                self._load_model(model_size)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            stats = {
                'cached_models': list(self.models.keys()),
                'cache_size': len(self.models),
                'max_cache_size': self.cache_config['max_models'],
                'model_usage': self.model_usage.copy(),
                'memory_usage': self._get_memory_usage()
            }
            
            # Add model sizes
            for model_size in self.models:
                if model_size in self.model_usage:
                    usage = self.model_usage[model_size]
                    stats['model_usage'][model_size]['idle_time'] = (
                        datetime.now() - usage['last_used']
                    ).total_seconds()
            
            return stats
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': process.memory_percent()
            }
        except ImportError:
            return {'error': 'psutil not available'}
    
    def clear_cache(self):
        """Clear all cached models"""
        with self._lock:
            logger.info("Clearing model cache")
            
            for model_size in list(self.models.keys()):
                self._unload_model(model_size)
            
            logger.info("Model cache cleared")
    
    def optimize_memory(self):
        """Optimize memory usage"""
        logger.info("Optimizing memory usage")
        
        # Force garbage collection
        gc.collect()
        
        # Clear CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("Memory optimization completed")

# Global model cache instance
model_cache = ModelCache()

def get_model_cache() -> ModelCache:
    """Get the global model cache instance"""
    return model_cache
