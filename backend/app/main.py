import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.database import get_db, engine
from app.database import Base

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("arenamind")

app = FastAPI(
    title="ArenaMind AI API",
    description="The Intelligent Stadium Operating System Core API",
    version="1.0.0"
)

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_db_check():
    logger.info("Initializing database tables...")
    try:
        # Create database tables if they do not exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Perform simple db execution check
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "environment": settings.APP_ENV,
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )
