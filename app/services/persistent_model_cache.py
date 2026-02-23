"""
Persistent Model Cache Manager for Whisper models
Ensures models are always cached and available for immediate use
"""

import os
import threading
import time
import logging
import pickle
import json
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import gc
import torch
from pathlib import Path

try:
    import whisper
except ImportError:
    whisper = None
    logging.warning("Whisper not available. Model caching will not work.")

logger = logging.getLogger(__name__)

class PersistentModelCache:
    """Enhanced model cache with persistent storage and always-on caching"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(PersistentModelCache, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.models: Dict[str, Any] = {}
        self.model_usage: Dict[str, Dict[str, Any]] = {}
        self.model_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Cache configuration
        self.cache_config = {
            'max_models': int(os.getenv('WHISPER_MODEL_CACHE_SIZE', 5)),  # Increased default
            'idle_timeout': int(os.getenv('MODEL_IDLE_TIMEOUT', 3600)),  # 1 hour
            'cleanup_interval': int(os.getenv('MODEL_CLEANUP_INTERVAL', 600)),  # 10 minutes
            'enable_gpu': os.getenv('ENABLE_GPU_ACCELERATION', 'true').lower() == 'true',
            'persistent_cache': os.getenv('PERSISTENT_MODEL_CACHE', 'true').lower() == 'true',
            'always_keep_models': os.getenv('ALWAYS_KEEP_MODELS', 'true').lower() == 'true',
            'warmup_models': os.getenv('WARMUP_MODELS', 'base,small,medium').split(','),
            'priority_models': os.getenv('PRIORITY_MODELS', 'base,small').split(',')
        }
        
        # Cache directory for persistent storage
        self.cache_dir = Path(os.getenv('MODEL_CACHE_DIR', 'model_cache'))
        self.cache_dir.mkdir(exist_ok=True)
        
        # Statistics
        self.stats = {
            'total_loads': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'evictions': 0,
            'startup_time': datetime.now()
        }
        
        self._cleanup_thread = None
        self._warmup_thread = None
        self._monitor_thread = None
        
        # Start background threads
        self._start_background_threads()
        self._initialized = True
        
        logger.info(f"PersistentModelCache initialized with config: {self.cache_config}")
    
    def _start_background_threads(self):
        """Start all background threads"""
        # Cleanup thread
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_models,
                daemon=True,
                name="ModelCacheCleanup"
            )
            self._cleanup_thread.start()
            logger.info("Model cache cleanup thread started")
        
        # Warmup thread
        if self._warmup_thread is None or not self._warmup_thread.is_alive():
            self._warmup_thread = threading.Thread(
                target=self._warmup_priority_models,
                daemon=True,
                name="ModelCacheWarmup"
            )
            self._warmup_thread.start()
            logger.info("Model cache warmup thread started")
        
        # Monitor thread
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._monitor_thread = threading.Thread(
                target=self._monitor_cache_health,
                daemon=True,
                name="ModelCacheMonitor"
            )
            self._monitor_thread.start()
            logger.info("Model cache monitor thread started")
    
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
        
        self.stats['total_loads'] += 1
        
        with self._lock:
            # Check if model is already cached
            if model_size in self.models:
                self.stats['cache_hits'] += 1
                self._update_usage(model_size)
                logger.info(f"Using cached model: {model_size}")
                return self.models[model_size]
            
            # Load new model
            self.stats['cache_misses'] += 1
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
            # Check if we need to evict models
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
            
            # Store metadata
            self.model_metadata[model_size] = {
                'load_time': load_time,
                'device': device,
                'loaded_at': datetime.now().isoformat(),
                'size_mb': self._estimate_model_size(model_size)
            }
            
            # Save to persistent cache if enabled
            if self.cache_config['persistent_cache']:
                self._save_model_metadata(model_size)
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model {model_size}: {e}")
            return None
    
    def _estimate_model_size(self, model_size: str) -> float:
        """Estimate model size in MB"""
        size_estimates = {
            'tiny': 39,
            'base': 74,
            'small': 244,
            'medium': 769,
            'large': 1550
        }
        return size_estimates.get(model_size, 100)
    
    def _update_usage(self, model_size: str, is_new: bool = False):
        """Update model usage statistics"""
        now = datetime.now()
        
        if is_new:
            self.model_usage[model_size] = {
                'first_used': now,
                'last_used': now,
                'access_count': 1,
                'total_load_time': 0
            }
        else:
            if model_size in self.model_usage:
                self.model_usage[model_size]['last_used'] = now
                self.model_usage[model_size]['access_count'] += 1
            else:
                self.model_usage[model_size] = {
                    'first_used': now,
                    'last_used': now,
                    'access_count': 1,
                    'total_load_time': 0
                }
    
    def _evict_least_used_model(self):
        """Evict the least recently used model from cache"""
        if not self.model_usage:
            return
        
        # Don't evict priority models if always_keep_models is enabled
        if self.cache_config['always_keep_models']:
            available_for_eviction = [
                model for model in self.model_usage.keys()
                if model not in self.cache_config['priority_models']
            ]
            if not available_for_eviction:
                logger.warning("All models are priority models, cannot evict")
                return
            eviction_candidates = available_for_eviction
        else:
            eviction_candidates = list(self.model_usage.keys())
        
        # Find least recently used model among candidates
        lru_model = min(
            [(model, usage) for model, usage in self.model_usage.items() 
             if model in eviction_candidates],
            key=lambda x: x[1]['last_used']
        )[0]
        
        logger.info(f"Evicting least used model: {lru_model}")
        self._unload_model(lru_model)
        self.stats['evictions'] += 1
    
    def _unload_model(self, model_size: str):
        """Unload a model from memory"""
        if model_size in self.models:
            try:
                # Clear model from memory
                del self.models[model_size]
                
                # Clear usage stats
                if model_size in self.model_usage:
                    del self.model_usage[model_size]
                
                # Clear metadata
                if model_size in self.model_metadata:
                    del self.model_metadata[model_size]
                
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
                
                # Skip cleanup if always_keep_models is enabled
                if self.cache_config['always_keep_models']:
                    continue
                
                with self._lock:
                    now = datetime.now()
                    idle_models = []
                    
                    for model_size, usage in self.model_usage.items():
                        idle_time = now - usage['last_used']
                        if idle_time.total_seconds() > self.cache_config['idle_timeout']:
                            # Don't clean up priority models
                            if model_size not in self.cache_config['priority_models']:
                                idle_models.append(model_size)
                    
                    # Unload idle models
                    for model_size in idle_models:
                        logger.info(f"Cleaning up idle model: {model_size}")
                        self._unload_model(model_size)
                        
            except Exception as e:
                logger.error(f"Error in model cleanup thread: {e}")
    
    def _warmup_priority_models(self):
        """Warm up priority models in background"""
        time.sleep(5)  # Wait for app to start
        
        try:
            warmup_models = self.cache_config['warmup_models']
            logger.info(f"Warming up models: {warmup_models}")
            
            for model_size in warmup_models:
                if model_size not in self.models:
                    logger.info(f"Warming up model: {model_size}")
                    self._load_model(model_size)
                    time.sleep(2)  # Stagger loading
                    
        except Exception as e:
            logger.error(f"Error in model warmup thread: {e}")
    
    def _monitor_cache_health(self):
        """Monitor cache health and performance"""
        while True:
            try:
                time.sleep(300)  # Check every 5 minutes
                
                with self._lock:
                    # Log cache statistics
                    hit_rate = (self.stats['cache_hits'] / max(self.stats['total_loads'], 1)) * 100
                    logger.info(f"Cache hit rate: {hit_rate:.1f}% ({self.stats['cache_hits']}/{self.stats['total_loads']})")
                    
                    # Check memory usage
                    memory_usage = self._get_memory_usage()
                    if memory_usage.get('percent', 0) > 90:
                        logger.warning(f"High memory usage: {memory_usage['percent']:.1f}%")
                    
                    # Ensure priority models are loaded
                    for model_size in self.cache_config['priority_models']:
                        if model_size not in self.models:
                            logger.info(f"Priority model {model_size} not loaded, loading now")
                            self._load_model(model_size)
                            
            except Exception as e:
                logger.error(f"Error in cache monitor thread: {e}")
    
    def _save_model_metadata(self, model_size: str):
        """Save model metadata to persistent storage"""
        try:
            metadata_file = self.cache_dir / f"{model_size}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(self.model_metadata.get(model_size, {}), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata for {model_size}: {e}")
    
    def preload_models(self, model_sizes: List[str]):
        """
        Preload specified models into cache
        
        Args:
            model_sizes: List of model sizes to preload
        """
        logger.info(f"Preloading models: {model_sizes}")
        
        for model_size in model_sizes:
            if model_size not in self.models:
                self._load_model(model_size)
                time.sleep(1)  # Stagger loading
    
    def ensure_models_loaded(self, model_sizes: List[str]):
        """
        Ensure specific models are loaded, load them if not
        
        Args:
            model_sizes: List of model sizes to ensure are loaded
        """
        with self._lock:
            for model_size in model_sizes:
                if model_size not in self.models:
                    logger.info(f"Ensuring model {model_size} is loaded")
                    self._load_model(model_size)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        with self._lock:
            stats = {
                'cached_models': list(self.models.keys()),
                'cache_size': len(self.models),
                'max_cache_size': self.cache_config['max_models'],
                'model_usage': self.model_usage.copy(),
                'model_metadata': self.model_metadata.copy(),
                'memory_usage': self._get_memory_usage(),
                'performance_stats': self.stats.copy(),
                'config': self.cache_config.copy()
            }
            
            # Add model sizes and idle times
            for model_size in self.models:
                if model_size in self.model_usage:
                    usage = self.model_usage[model_size]
                    stats['model_usage'][model_size]['idle_time'] = (
                        datetime.now() - usage['last_used']
                    ).total_seconds()
            
            # Calculate hit rate
            total_loads = max(self.stats['total_loads'], 1)
            stats['hit_rate'] = (self.stats['cache_hits'] / total_loads) * 100
            
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
    
    def force_reload_model(self, model_size: str):
        """Force reload a specific model"""
        with self._lock:
            if model_size in self.models:
                self._unload_model(model_size)
            self._load_model(model_size)
    
    def get_model_status(self, model_size: str) -> Dict[str, Any]:
        """Get detailed status of a specific model"""
        with self._lock:
            status = {
                'loaded': model_size in self.models,
                'usage': self.model_usage.get(model_size, {}),
                'metadata': self.model_metadata.get(model_size, {}),
                'is_priority': model_size in self.cache_config['priority_models']
            }
            
            if model_size in self.models:
                status['idle_time'] = (
                    datetime.now() - self.model_usage[model_size]['last_used']
                ).total_seconds()
            
            return status

# Global persistent model cache instance
persistent_model_cache = PersistentModelCache()

def get_persistent_model_cache() -> PersistentModelCache:
    """Get the global persistent model cache instance"""
    return persistent_model_cache
