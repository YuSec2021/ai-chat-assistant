"""MongoDB database connection and operations"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional, Dict, Any
from uuid import uuid4
from datetime import datetime
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
    await db.conversations.create_index("user_id")

    # Create indexes for users
    await db.users.create_index("username", unique=True)
    await db.users.create_index("email", unique=True, sparse=True)
    await db.users.create_index("created_at")

    logger.info("Database indexes created")


# ==================== User Operations ====================

async def create_user(
    username: str,
    password_hash: str,
    subscription_level: str = "free",
    role: str = "user"
) -> Dict[str, Any]:
    """
    Create a new user.

    Args:
        username: Username
        password_hash: Hashed password
        subscription_level: Subscription level (free, gold, diamond)
        role: User role (user, admin)

    Returns:
        Created user document
    """
    db = mongodb.get_db()
    user_id = str(uuid4())

    user_doc = {
        "id": user_id,
        "username": username,
        "password_hash": password_hash,
        "subscription_level": subscription_level,
        "role": role,
        "is_active": True,
        "is_banned": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_login": None
    }

    await db.users.insert_one(user_doc)
    logger.info("User created", user_id=user_id, username=username)
    return user_doc


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user by ID.

    Args:
        user_id: User UUID

    Returns:
        User document or None
    """
    db = mongodb.get_db()
    return await db.users.find_one({"id": user_id})


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """
    Get user by username.

    Args:
        username: Username

    Returns:
        User document or None
    """
    db = mongodb.get_db()
    return await db.users.find_one({"username": username})


async def update_user_last_login(user_id: str) -> None:
    """
    Update user's last login timestamp.

    Args:
        user_id: User UUID
    """
    db = mongodb.get_db()
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"last_login": datetime.utcnow()}}
    )


async def list_users(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None
) -> tuple[list[Dict[str, Any]], int]:
    """
    List users with pagination and search.

    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        search: Search string for username

    Returns:
        Tuple of (user list, total count)
    """
    db = mongodb.get_db()

    # Build query
    query = {}
    if search:
        query["username"] = {"$regex": search, "$options": "i"}

    # Get total count
    total = await db.users.count_documents(query)

    # Get users with pagination
    cursor = db.users.find(query).skip(skip).limit(limit).sort("created_at", -1)
    users = await cursor.to_list(length=limit)

    # Remove password hash from results
    for user in users:
        user.pop("password_hash", None)

    return users, total


async def update_user(user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update user fields.

    Args:
        user_id: User UUID
        updates: Fields to update

    Returns:
        Updated user document or None
    """
    db = mongodb.get_db()
    updates["updated_at"] = datetime.utcnow()

    result = await db.users.update_one(
        {"id": user_id},
        {"$set": updates}
    )

    if result.modified_count > 0:
        return await get_user_by_id(user_id)
    return None


async def ban_user(user_id: str) -> bool:
    """
    Ban a user.

    Args:
        user_id: User UUID

    Returns:
        True if successful
    """
    db = mongodb.get_db()
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_banned": True, "updated_at": datetime.utcnow()}}
    )
    return result.modified_count > 0


async def unban_user(user_id: str) -> bool:
    """
    Unban a user.

    Args:
        user_id: User UUID

    Returns:
        True if successful
    """
    db = mongodb.get_db()
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_banned": False, "updated_at": datetime.utcnow()}}
    )
    return result.modified_count > 0


# ==================== Conversation Operations (with user_id) ====================

async def create_conversation(
    user_id: str,
    title: str = "New Conversation"
) -> Dict[str, Any]:
    """
    Create a new conversation for a user.

    Args:
        user_id: User UUID
        title: Conversation title

    Returns:
        Created conversation document
    """
    db = mongodb.get_db()
    conv_id = str(uuid4())

    conv_doc = {
        "id": conv_id,
        "user_id": user_id,
        "title": title,
        "messages": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "metadata": {}
    }

    await db.conversations.insert_one(conv_doc)
    return conv_doc


async def get_user_conversations(
    user_id: str,
    skip: int = 0,
    limit: int = 50
) -> list[Dict[str, Any]]:
    """
    Get all conversations for a user.

    Args:
        user_id: User UUID
        skip: Number of conversations to skip
        limit: Maximum number of conversations to return

    Returns:
        List of conversation documents
    """
    db = mongodb.get_db()

    cursor = db.conversations.find(
        {"user_id": user_id}
    ).skip(skip).limit(limit).sort("updated_at", -1)

    return await cursor.to_list(length=limit)


async def get_conversation_for_user(
    conv_id: str,
    user_id: str
) -> Optional[Dict[str, Any]]:
    """
    Get a conversation by ID (with user ownership check).

    Args:
        conv_id: Conversation UUID
        user_id: User UUID

    Returns:
        Conversation document or None
    """
    db = mongodb.get_db()
    return await db.conversations.find_one({"id": conv_id, "user_id": user_id})


async def add_message_to_conversation(
    conv_id: str,
    user_id: str,
    role: str,
    content: str,
    attachments: list = None
) -> Optional[Dict[str, Any]]:
    """
    Add a message to a conversation (with user ownership check).

    Args:
        conv_id: Conversation UUID
        user_id: User UUID
        role: Message role (user, assistant, system)
        content: Message content
        attachments: List of attachment IDs

    Returns:
        Updated conversation document or None
    """
    db = mongodb.get_db()

    from datetime import datetime
    from uuid import uuid4

    message = {
        "id": str(uuid4()),
        "role": role,
        "content": content,
        "attachments": attachments or [],
        "metadata": {},
        "timestamp": datetime.utcnow()
    }

    result = await db.conversations.update_one(
        {"id": conv_id, "user_id": user_id},
        {
            "$push": {"messages": message},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )

    if result.modified_count > 0:
        return await get_conversation_for_user(conv_id, user_id)
    return None
