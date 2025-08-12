from supabase import create_client, Client as SupabaseClient
from app.core.config import settings
from typing import Dict, Any, List, Optional

class SupabaseManager:
    _instance: SupabaseClient = None
    
    @classmethod
    def get_client(cls) -> SupabaseClient:
        if cls._instance is None:
            cls._instance = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        return cls._instance
    
    @classmethod
    async def query(
        cls, 
        table: str, 
        method: str = 'select', 
        query_params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Generic query method for Supabase
        
        Args:
            table: Table name
            method: Query method (select, insert, update, delete)
            query_params: Query parameters (filters, etc.)
            data: Data for insert/update operations
            
        Returns:
            Query result
        """
        client = cls.get_client()
        query = client.table(table)
        
        # Apply query parameters (filters, etc.)
        if query_params:
            for key, value in query_params.items():
                if key == 'eq':
                    for k, v in value.items():
                        query = query.eq(k, v)
                # Add other query methods as needed (gt, lt, ilike, etc.)
        
        # Execute the query
        if method == 'select':
            result = query.execute()
        elif method == 'insert':
            result = query.insert(data).execute()
        elif method == 'update':
            result = query.update(data).execute()
        elif method == 'delete':
            result = query.delete().execute()
        else:
            raise ValueError(f"Unsupported query method: {method}")
            
        return result.data if hasattr(result, 'data') else result
    
    @classmethod
    async def upload_file(cls, bucket: str, file_path: str, file_data: bytes) -> str:
        """Upload a file to Supabase Storage"""
        client = cls.get_client()
        result = client.storage.from_(bucket).upload(file_path, file_data)
        return f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{file_path}"
    
    @classmethod
    async def get_embedding(cls, text: str) -> List[float]:
        """Get embedding for text using Supabase's pgvector"""
        client = cls.get_client()
        result = client.rpc('get_embedding', {'text': text}).execute()
        return result.data[0]['embedding'] if result.data else None
