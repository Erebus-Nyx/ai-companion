"""
Global model registry to prevent reloading models within the same session.
"""

import threading
from typing import Dict, Any, Optional

class GlobalModelRegistry:
    """Thread-safe global registry for loaded models"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._models = {}
                    cls._instance._init_lock = threading.Lock()
        return cls._instance
    
    def get_model(self, model_key: str) -> Optional[Any]:
        """Get a model from the registry"""
        with self._init_lock:
            return self._models.get(model_key)
    
    def set_model(self, model_key: str, model: Any):
        """Set a model in the registry"""
        with self._init_lock:
            self._models[model_key] = model
    
    def has_model(self, model_key: str) -> bool:
        """Check if model is in registry"""
        with self._init_lock:
            return model_key in self._models
    
    def clear(self):
        """Clear all models (for testing)"""
        with self._init_lock:
            self._models.clear()

# Global instance
model_registry = GlobalModelRegistry()
