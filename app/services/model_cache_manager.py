"""
Model Cache Manager - Unified interface for model caching
Provides seamless integration between old and new caching systems
"""

import os
import logging
from typing import Dict, Any, List, Optional
from app.config import Config

logger = logging.getLogger(__name__)

class ModelCacheManager:
    """Unified model cache manager that handles both old and new caching systems"""
    
    _instance = None
    _cache_system = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelCacheManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.config = Config()
        self._initialize_cache_system()
        self._initialized = True
    
    def _initialize_cache_system(self):
        """Initialize the appropriate cache system based on configuration"""
        try:
            if self.config.PERSISTENT_MODEL_CACHE:
                from app.services.persistent_model_cache import get_persistent_model_cache
                self._cache_system = get_persistent_model_cache()
                logger.info("Using persistent model cache system")
            else:
                from app.services.model_cache import get_model_cache
                self._cache_system = get_model_cache()
                logger.info("Using standard model cache system")
        except Exception as e:
            logger.error(f"Failed to initialize cache system: {e}")
            # Fallback to standard cache
            try:
                from app.services.model_cache import get_model_cache
                self._cache_system = get_model_cache()
                logger.info("Fell back to standard model cache system")
            except Exception as e2:
                logger.error(f"Failed to initialize fallback cache: {e2}")
                self._cache_system = None
    
    def get_model(self, model_size: str) -> Optional[Any]:
        """Get a model from cache"""
        if not self._cache_system:
            logger.error("No cache system available")
            return None
        
        return self._cache_system.get_model(model_size)
    
    def preload_models(self, model_sizes: List[str]):
        """Preload models into cache"""
        if not self._cache_system:
            logger.error("No cache system available")
            return
        
        self._cache_system.preload_models(model_sizes)
    
    def ensure_models_loaded(self, model_sizes: List[str]):
        """Ensure specific models are loaded"""
        if not self._cache_system:
            logger.error("No cache system available")
            return
        
        if hasattr(self._cache_system, 'ensure_models_loaded'):
            self._cache_system.ensure_models_loaded(model_sizes)
        else:
            # Fallback for old cache system
            self._cache_system.preload_models(model_sizes)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self._cache_system:
            return {'error': 'No cache system available'}
        
        return self._cache_system.get_cache_stats()
    
    def clear_cache(self):
        """Clear all cached models"""
        if not self._cache_system:
            logger.error("No cache system available")
            return
        
        self._cache_system.clear_cache()
    
    def optimize_memory(self):
        """Optimize memory usage"""
        if not self._cache_system:
            logger.error("No cache system available")
            return
        
        self._cache_system.optimize_memory()
    
    def force_reload_model(self, model_size: str):
        """Force reload a specific model"""
        if not self._cache_system:
            logger.error("No cache system available")
            return
        
        if hasattr(self._cache_system, 'force_reload_model'):
            self._cache_system.force_reload_model(model_size)
        else:
            # Fallback for old cache system
            self.clear_cache()
            self.preload_models([model_size])
    
    def get_model_status(self, model_size: str) -> Dict[str, Any]:
        """Get detailed status of a specific model"""
        if not self._cache_system:
            return {'error': 'No cache system available'}
        
        if hasattr(self._cache_system, 'get_model_status'):
            return self._cache_system.get_model_status(model_size)
        else:
            # Fallback for old cache system
            stats = self._cache_system.get_cache_stats()
            return {
                'loaded': model_size in stats.get('cached_models', []),
                'usage': stats.get('model_usage', {}).get(model_size, {}),
                'is_priority': model_size in self.config.PRIORITY_MODELS
            }
    
    def warmup_priority_models(self):
        """Warm up priority models"""
        if not self._cache_system:
            logger.error("No cache system available")
            return
        
        priority_models = self.config.PRIORITY_MODELS
        logger.info(f"Warming up priority models: {priority_models}")
        self.ensure_models_loaded(priority_models)
    
    def get_available_models(self) -> List[str]:
        """Get list of available model sizes"""
        return ['tiny', 'base', 'small', 'medium', 'large']
    
    def is_model_loaded(self, model_size: str) -> bool:
        """Check if a model is currently loaded"""
        if not self._cache_system:
            return False
        
        stats = self._cache_system.get_cache_stats()
        return model_size in stats.get('cached_models', [])
    
    def get_loaded_models(self) -> List[str]:
        """Get list of currently loaded models"""
        if not self._cache_system:
            return []
        
        stats = self._cache_system.get_cache_stats()
        return stats.get('cached_models', [])
    
    def get_cache_health(self) -> Dict[str, Any]:
        """Get cache health information"""
        if not self._cache_system:
            return {'status': 'error', 'message': 'No cache system available'}
        
        try:
            stats = self._cache_system.get_cache_stats()
            
            # Calculate health metrics
            total_models = len(self.get_available_models())
            loaded_models = len(stats.get('cached_models', []))
            priority_models = len(self.config.PRIORITY_MODELS)
            loaded_priority = len([m for m in self.config.PRIORITY_MODELS if m in stats.get('cached_models', [])])
            
            health = {
                'status': 'healthy',
                'total_models': total_models,
                'loaded_models': loaded_models,
                'priority_models': priority_models,
                'loaded_priority': loaded_priority,
                'priority_coverage': (loaded_priority / priority_models * 100) if priority_models > 0 else 0,
                'memory_usage': stats.get('memory_usage', {}),
                'hit_rate': stats.get('hit_rate', 0),
                'cache_size': stats.get('cache_size', 0),
                'max_cache_size': stats.get('max_cache_size', 0)
            }
            
            # Determine health status
            if loaded_priority < priority_models:
                health['status'] = 'warning'
                health['message'] = f'Only {loaded_priority}/{priority_models} priority models loaded'
            elif stats.get('hit_rate', 0) < 50:
                health['status'] = 'warning'
                health['message'] = f'Low cache hit rate: {stats.get("hit_rate", 0):.1f}%'
            elif stats.get('memory_usage', {}).get('percent', 0) > 90:
                health['status'] = 'warning'
                health['message'] = f'High memory usage: {stats.get("memory_usage", {}).get("percent", 0):.1f}%'
            else:
                health['message'] = 'All systems operational'
            
            return health
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to get cache health: {e}'
            }

# Global model cache manager instance
model_cache_manager = ModelCacheManager()

def get_model_cache_manager() -> ModelCacheManager:
    """Get the global model cache manager instance"""
    return model_cache_manager
