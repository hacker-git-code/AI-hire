from sqlalchemy import create_engine
from app.core.config import settings
from app.core.database import Base
from app.models.candidate import Candidate
from app.models.interview import Interview

def init_db():
    """Initialize the database."""
    try:
        # Create database engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise

if __name__ == "__main__":
    init_db() 