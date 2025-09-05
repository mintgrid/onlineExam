"""
Firebase Configuration and Database Helper Functions
"""

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import firestore as gcp_firestore
from datetime import datetime, timezone
import os
import json
import logging
from functools import lru_cache
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseDB:
    """Firebase Firestore database helper class with performance optimizations"""
    
    def __init__(self):
        self.db = None
        self._cache = {}
        self._cache_ttl = 30  # 30 seconds cache
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            if not firebase_admin._apps:
                # For production, use service account key
                if os.getenv('FIREBASE_SERVICE_ACCOUNT'):
                    cred_dict = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT'))
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                elif os.getenv('GOOGLE_CLOUD_PROJECT'):
                    # Running on Google Cloud - try Secret Manager first
                    try:
                        from google.cloud import secretmanager
                        client = secretmanager.SecretManagerServiceClient()
                        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
                        secret_name = f"projects/{project_id}/secrets/firebase-service-account/versions/latest"
                        response = client.access_secret_version(request={"name": secret_name})
                        secret_data = response.payload.data.decode("UTF-8")
                        cred_dict = json.loads(secret_data)
                        cred = credentials.Certificate(cred_dict)
                        firebase_admin.initialize_app(cred)
                        logger.info("Firebase initialized using Secret Manager")
                    except Exception as secret_error:
                        logger.warning(f"Secret Manager failed: {secret_error}, falling back to default credentials")
                        # Use default credentials (works on Google Cloud)
                        firebase_admin.initialize_app()
                        logger.info("Firebase initialized using default credentials")
                else:
                    # For development, use service account file
                    service_account_path = 'onlineexam-f01cd-firebase-adminsdk-fbsvc-41ab6e69cf.json'
                    if os.path.exists(service_account_path):
                        cred = credentials.Certificate(service_account_path)
                        firebase_admin.initialize_app(cred)
                    else:
                        # Fallback to firebase-service-account.json
                        fallback_path = 'firebase-service-account.json'
                        if os.path.exists(fallback_path):
                            cred = credentials.Certificate(fallback_path)
                            firebase_admin.initialize_app(cred)
                        else:
                            # Use default credentials (works on Google Cloud)
                            firebase_admin.initialize_app()
                
                logger.info("Firebase initialized successfully")
            
            self.db = firestore.client()
            
        except Exception as e:
            logger.error(f"Firebase initialization error: {e}")
            self.db = None
    
    def _get_cache_key(self, collection_name, filters=None, order_by=None, limit=None):
        """Generate cache key for query"""
        key_parts = [collection_name]
        if filters:
            key_parts.append(str(sorted(filters)))
        if order_by:
            key_parts.append(str(order_by))
        if limit:
            key_parts.append(str(limit))
        return '|'.join(key_parts)
    
    def _is_cache_valid(self, cache_entry):
        """Check if cache entry is still valid"""
        return time.time() - cache_entry['timestamp'] < self._cache_ttl
    
    def _clear_collection_cache(self, collection_name):
        """Clear cache entries for a collection"""
        keys_to_remove = []
        for key in self._cache:
            if key.startswith(collection_name + '|'):
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del self._cache[key]
    
    def add_document(self, collection_name, document_data, document_id=None):
        """Add a document to a collection"""
        try:
            collection_ref = self.db.collection(collection_name)
            
            # Add timestamp
            document_data['created_at'] = datetime.now(timezone.utc)
            document_data['updated_at'] = datetime.now(timezone.utc)
            
            if document_id:
                doc_ref = collection_ref.document(document_id)
                doc_ref.set(document_data)
                return document_id
            else:
                doc_ref = collection_ref.add(document_data)
                result = doc_ref[1].id
                # Clear cache when adding documents
                self._clear_collection_cache(collection_name)
                return result
                
        except Exception as e:
            logger.error(f"Error adding document to {collection_name}: {e}")
            return None
    
    def get_document(self, collection_name, document_id):
        """Get a document by ID"""
        try:
            doc_ref = self.db.collection(collection_name).document(document_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            return None
            
        except Exception as e:
            logger.error(f"Error getting document {document_id} from {collection_name}: {e}")
            return None
    
    def get_documents(self, collection_name, filters=None, order_by=None, limit=None):
        """Get multiple documents with optional filters and caching"""
        # Check cache first for read-heavy queries
        cache_key = self._get_cache_key(collection_name, filters, order_by, limit)
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
            return self._cache[cache_key]['data']
        
        try:
            query = self.db.collection(collection_name)
            
            # Apply filters
            if filters:
                for field, operator, value in filters:
                    query = query.where(filter=gcp_firestore.FieldFilter(field, operator, value))
            
            # Apply ordering
            if order_by:
                for field, direction in order_by:
                    # Convert direction to Firestore format
                    if direction.lower() in ['desc', 'descending']:
                        from google.cloud.firestore import Query
                        query = query.order_by(field, direction=Query.DESCENDING)
                    else:
                        from google.cloud.firestore import Query
                        query = query.order_by(field, direction=Query.ASCENDING)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            result = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                result.append(data)
            
            # Cache the result
            self._cache[cache_key] = {
                'data': result,
                'timestamp': time.time()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting documents from {collection_name}: {e}")
            return []
    
    def update_document(self, collection_name, document_id, update_data):
        """Update a document"""
        try:
            doc_ref = self.db.collection(collection_name).document(document_id)
            update_data['updated_at'] = datetime.now(timezone.utc)
            doc_ref.update(update_data)
            # Clear cache when updating documents
            self._clear_collection_cache(collection_name)
            return True
            
        except Exception as e:
            logger.error(f"Error updating document {document_id} in {collection_name}: {e}")
            return False
    
    def delete_document(self, collection_name, document_id):
        """Delete a document"""
        try:
            doc_ref = self.db.collection(collection_name).document(document_id)
            doc_ref.delete()
            # Clear cache when deleting documents
            self._clear_collection_cache(collection_name)
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id} from {collection_name}: {e}")
            return False
    
    def get_document_by_field(self, collection_name, field, value):
        """Get a document by a specific field value"""
        try:
            docs = self.db.collection(collection_name).where(filter=gcp_firestore.FieldFilter(field, '==', value)).limit(1).stream()
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting document by {field} from {collection_name}: {e}")
            return None
    
    def batch_write(self, operations):
        """Execute multiple operations in a batch"""
        try:
            batch = self.db.batch()
            
            for operation in operations:
                op_type = operation['type']
                collection = operation['collection']
                doc_id = operation['doc_id']
                
                doc_ref = self.db.collection(collection).document(doc_id)
                
                if op_type == 'set':
                    data = operation['data']
                    data['created_at'] = datetime.now(timezone.utc)
                    data['updated_at'] = datetime.now(timezone.utc)
                    batch.set(doc_ref, data)
                elif op_type == 'update':
                    data = operation['data']
                    data['updated_at'] = datetime.now(timezone.utc)
                    batch.update(doc_ref, data)
                elif op_type == 'delete':
                    batch.delete(doc_ref)
            
            batch.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error in batch write: {e}")
            return False

# Global Firebase instance
firebase_db = FirebaseDB()

# Collection names
COLLECTIONS = {
    'USERS': 'users',
    'EXAMS': 'exams', 
    'QUESTIONS': 'questions',
    'EXAM_PERMISSIONS': 'examPermissions',
    'EXAM_RESULTS': 'examResults',
    'SETTINGS': 'settings'
}