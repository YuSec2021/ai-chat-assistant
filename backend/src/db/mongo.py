"""MongoDB database connection and operations"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from src.config import settings
import structlog

logger = structlog.get_logger(__name__)


class MongoDB:
    """MongoDB connection manager"""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.database = self.client[settings.database_name]

            # Test connection
            await self.database.command("ping")

            logger.info("Connected to MongoDB", database=settings.database_name)

        except Exception as e:
            logger.error("Failed to connect to MongoDB", error=str(e))
            raise

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    def get_db(self) -> AsyncIOMotorDatabase:
        """Get database instance"""
        if self.database is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.database


# Global MongoDB instance
mongodb = MongoDB()


async def get_database() -> AsyncIOMotorDatabase:
    """Dependency to get database instance"""
    return mongodb.get_db()


async def init_db():
    """Initialize database indexes"""
    db = mongodb.get_db()

    # Create indexes for conversations
    await db.conversations.create_index("created_at")
    await db.conversations.create_index("updated_at")
    await db.conversations.create_index("title")

    logger.info("Database indexes created")
