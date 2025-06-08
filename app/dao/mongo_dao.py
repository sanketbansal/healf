"""
Generic MongoDB Data Access Object (DAO)
Provides reusable MongoDB operations for document storage, querying, and aggregation
"""

import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import IndexModel, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError
from app.config import settings

class MongoDAO:
    """Generic MongoDB DAO for all MongoDB operations"""
    
    def __init__(self):
        self._mongo_client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
        
    async def get_client(self) -> AsyncIOMotorClient:
        """Get MongoDB client with connection pooling"""
        if self._mongo_client is None:
            self._mongo_client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                maxPoolSize=20,
                minPoolSize=5,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
        return self._mongo_client
    
    async def get_database(self) -> AsyncIOMotorDatabase:
        """Get MongoDB database"""
        if self._database is None:
            client = await self.get_client()
            self._database = client.get_default_database()
        return self._database
    
    async def get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """Get MongoDB collection"""
        database = await self.get_database()
        return database[collection_name]
    
    # =================== Document Operations ===================
    
    async def insert_one(self, collection_name: str, document: Dict[str, Any]) -> Optional[str]:
        """Insert a single document"""
        try:
            collection = await self.get_collection(collection_name)
            
            # Add timestamps
            document['created_at'] = datetime.now(timezone.utc)
            document['updated_at'] = datetime.now(timezone.utc)
            
            result = await collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            print(f"MongoDB INSERT_ONE error in {collection_name}: {e}")
            return None
    
    async def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents"""
        try:
            collection = await self.get_collection(collection_name)
            
            # Add timestamps to all documents
            now = datetime.now(timezone.utc)
            for doc in documents:
                doc['created_at'] = now
                doc['updated_at'] = now
            
            result = await collection.insert_many(documents)
            return [str(id) for id in result.inserted_ids]
        except Exception as e:
            print(f"MongoDB INSERT_MANY error in {collection_name}: {e}")
            return []
    
    async def find_one(self, collection_name: str, filter_dict: Dict[str, Any], 
                      projection: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Find a single document"""
        try:
            collection = await self.get_collection(collection_name)
            document = await collection.find_one(filter_dict, projection)
            
            if document:
                # Convert ObjectId to string
                document['_id'] = str(document['_id'])
                return document
            return None
        except Exception as e:
            print(f"MongoDB FIND_ONE error in {collection_name}: {e}")
            return None
    
    async def find_many(self, collection_name: str, filter_dict: Dict[str, Any] = None,
                       projection: Optional[Dict[str, Any]] = None, 
                       sort: Optional[List[tuple]] = None,
                       limit: Optional[int] = None, 
                       skip: Optional[int] = None) -> List[Dict[str, Any]]:
        """Find multiple documents"""
        try:
            collection = await self.get_collection(collection_name)
            
            if filter_dict is None:
                filter_dict = {}
            
            cursor = collection.find(filter_dict, projection)
            
            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            
            documents = []
            async for document in cursor:
                document['_id'] = str(document['_id'])
                documents.append(document)
            
            return documents
        except Exception as e:
            print(f"MongoDB FIND_MANY error in {collection_name}: {e}")
            return []
    
    async def update_one(self, collection_name: str, filter_dict: Dict[str, Any], 
                        update_dict: Dict[str, Any], upsert: bool = False) -> bool:
        """Update a single document"""
        try:
            collection = await self.get_collection(collection_name)
            
            # Add update timestamp
            if '$set' not in update_dict:
                update_dict = {'$set': update_dict}
            
            update_dict['$set']['updated_at'] = datetime.now(timezone.utc)
            
            result = await collection.update_one(filter_dict, update_dict, upsert=upsert)
            return result.modified_count > 0 or (upsert and result.upserted_id is not None)
        except Exception as e:
            print(f"MongoDB UPDATE_ONE error in {collection_name}: {e}")
            return False
    
    async def update_many(self, collection_name: str, filter_dict: Dict[str, Any], 
                         update_dict: Dict[str, Any]) -> int:
        """Update multiple documents"""
        try:
            collection = await self.get_collection(collection_name)
            
            # Add update timestamp
            if '$set' not in update_dict:
                update_dict = {'$set': update_dict}
            
            update_dict['$set']['updated_at'] = datetime.now(timezone.utc)
            
            result = await collection.update_many(filter_dict, update_dict)
            return result.modified_count
        except Exception as e:
            print(f"MongoDB UPDATE_MANY error in {collection_name}: {e}")
            return 0
    
    async def delete_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> bool:
        """Delete a single document"""
        try:
            collection = await self.get_collection(collection_name)
            result = await collection.delete_one(filter_dict)
            return result.deleted_count > 0
        except Exception as e:
            print(f"MongoDB DELETE_ONE error in {collection_name}: {e}")
            return False
    
    async def delete_many(self, collection_name: str, filter_dict: Dict[str, Any]) -> int:
        """Delete multiple documents"""
        try:
            collection = await self.get_collection(collection_name)
            result = await collection.delete_many(filter_dict)
            return result.deleted_count
        except Exception as e:
            print(f"MongoDB DELETE_MANY error in {collection_name}: {e}")
            return 0
    
    async def count_documents(self, collection_name: str, filter_dict: Dict[str, Any] = None) -> int:
        """Count documents matching filter"""
        try:
            collection = await self.get_collection(collection_name)
            if filter_dict is None:
                filter_dict = {}
            return await collection.count_documents(filter_dict)
        except Exception as e:
            print(f"MongoDB COUNT_DOCUMENTS error in {collection_name}: {e}")
            return 0
    
    # =================== Advanced Operations ===================
    
    async def aggregate(self, collection_name: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run aggregation pipeline"""
        try:
            collection = await self.get_collection(collection_name)
            cursor = collection.aggregate(pipeline)
            
            results = []
            async for document in cursor:
                if '_id' in document:
                    document['_id'] = str(document['_id'])
                results.append(document)
            
            return results
        except Exception as e:
            print(f"MongoDB AGGREGATE error in {collection_name}: {e}")
            return []
    
    async def distinct(self, collection_name: str, field: str, 
                      filter_dict: Dict[str, Any] = None) -> List[Any]:
        """Get distinct values for a field"""
        try:
            collection = await self.get_collection(collection_name)
            if filter_dict is None:
                filter_dict = {}
            return await collection.distinct(field, filter_dict)
        except Exception as e:
            print(f"MongoDB DISTINCT error in {collection_name}: {e}")
            return []
    
    async def find_one_and_update(self, collection_name: str, filter_dict: Dict[str, Any],
                                 update_dict: Dict[str, Any], return_document: str = 'after',
                                 upsert: bool = False) -> Optional[Dict[str, Any]]:
        """Find and update a document atomically"""
        try:
            from pymongo import ReturnDocument
            collection = await self.get_collection(collection_name)
            
            # Add update timestamp
            if '$set' not in update_dict:
                update_dict = {'$set': update_dict}
            
            update_dict['$set']['updated_at'] = datetime.now(timezone.utc)
            
            return_doc = ReturnDocument.AFTER if return_document == 'after' else ReturnDocument.BEFORE
            
            document = await collection.find_one_and_update(
                filter_dict, update_dict, return_document=return_doc, upsert=upsert
            )
            
            if document:
                document['_id'] = str(document['_id'])
                return document
            return None
        except Exception as e:
            print(f"MongoDB FIND_ONE_AND_UPDATE error in {collection_name}: {e}")
            return None
    
    # =================== Index Operations ===================
    
    async def create_index(self, collection_name: str, keys: Union[str, List[tuple]], 
                          unique: bool = False, background: bool = True) -> bool:
        """Create an index"""
        try:
            collection = await self.get_collection(collection_name)
            
            if isinstance(keys, str):
                keys = [(keys, ASCENDING)]
            
            index_model = IndexModel(keys, unique=unique, background=background)
            await collection.create_indexes([index_model])
            return True
        except Exception as e:
            print(f"MongoDB CREATE_INDEX error in {collection_name}: {e}")
            return False
    
    async def list_indexes(self, collection_name: str) -> List[Dict[str, Any]]:
        """List all indexes for a collection"""
        try:
            collection = await self.get_collection(collection_name)
            indexes = []
            async for index in collection.list_indexes():
                indexes.append(index)
            return indexes
        except Exception as e:
            print(f"MongoDB LIST_INDEXES error in {collection_name}: {e}")
            return []
    
    async def drop_index(self, collection_name: str, index_name: str) -> bool:
        """Drop an index"""
        try:
            collection = await self.get_collection(collection_name)
            await collection.drop_index(index_name)
            return True
        except Exception as e:
            print(f"MongoDB DROP_INDEX error in {collection_name}: {e}")
            return False
    
    # =================== Collection Operations ===================
    
    async def create_collection(self, collection_name: str) -> bool:
        """Create a collection"""
        try:
            database = await self.get_database()
            await database.create_collection(collection_name)
            return True
        except Exception as e:
            print(f"MongoDB CREATE_COLLECTION error for {collection_name}: {e}")
            return False
    
    async def drop_collection(self, collection_name: str) -> bool:
        """Drop a collection"""
        try:
            collection = await self.get_collection(collection_name)
            await collection.drop()
            return True
        except Exception as e:
            print(f"MongoDB DROP_COLLECTION error for {collection_name}: {e}")
            return False
    
    async def list_collections(self) -> List[str]:
        """List all collections"""
        try:
            database = await self.get_database()
            collections = await database.list_collection_names()
            return collections
        except Exception as e:
            print(f"MongoDB LIST_COLLECTIONS error: {e}")
            return []
    
    # =================== Utility Operations ===================
    
    async def ping(self) -> bool:
        """Test MongoDB connection"""
        try:
            client = await self.get_client()
            await client.admin.command('ping')
            return True
        except Exception as e:
            print(f"MongoDB PING error: {e}")
            return False
    
    async def get_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            collection = await self.get_collection(collection_name)
            stats = await collection.aggregate([{"$collStats": {"storageStats": {}}}]).to_list(1)
            return stats[0] if stats else {}
        except Exception as e:
            print(f"MongoDB STATS error for {collection_name}: {e}")
            return {}
    
    async def close(self):
        """Close MongoDB connection"""
        if self._mongo_client:
            self._mongo_client.close()

# Singleton instance
_mongo_dao_instance = None

def get_mongo_dao() -> MongoDAO:
    """Get singleton MongoDAO instance"""
    global _mongo_dao_instance
    if _mongo_dao_instance is None:
        _mongo_dao_instance = MongoDAO()
    return _mongo_dao_instance 