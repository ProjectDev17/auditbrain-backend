import logging
import os
from datetime import datetime
from pymongo import MongoClient
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
import json

logger = logging.getLogger(__name__)

class MongoLogService:
    _instance = None
    _client = None
    _db = None
    _collection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoLogService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        try:
            mongo_uri = getattr(settings, 'MONGO_URI', 'mongodb://localhost:27017/')
            self._client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
            self._db = self._client.get_database('auditbrain_logs')
            self._collection = self._db.get_collection('audit_logs')
        except Exception as e:
            logger.error(f"Error initializing MongoDB connection: {e}")
            self._collection = None

    def _get_user_repr(self, user):
        if not user or not user.is_authenticated:
            return 'system/anonymous'
        return str(user.id) # Or username

    def log_action(self, collection_name, action, data, user=None, resource_id=None):
        """
        Registra una acción en MongoDB.
        
        :param collection_name: Nombre de la entidad (ej. 'Audit')
        :param action: 'CREATE', 'UPDATE', 'DELETE'
        :param data: Diccionario con los datos relevantes (snapshot o diff)
        :param user: Instancia de User o string
        :param resource_id: ID del recurso afectado
        """
        if self._collection is None:
            # Intentar reconectar o loguear error
            try:
                self._initialize()
            except:
                pass
            
            if self._collection is None:
                logger.warning("MongoDB unavailable. Log lost.")
                return

        log_entry = {
            'timestamp': datetime.utcnow(),
            'action': action,
            'entity': collection_name,
            'resource_id': str(resource_id) if resource_id else None,
            'user': self._get_user_repr(user),
            'payload': data
        }

        try:
            # Asegurar que la data es serializable
            # json.loads(json.dumps(...)) es un truco rápido para limpiar objetos no serializables si usamos DjangoJSONEncoder
            # o podemos confiar en que data son dicts simples.
            self._collection.insert_one(log_entry)
        except Exception as e:
            logger.error(f"Failed to write to MongoDB: {e}")

# Instancia global
audit_logger = MongoLogService()
