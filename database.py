import os
import json
import logging
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import motor.motor_asyncio
from config import MONGO_URL, MONGO_DB_NAME, DATABASE_PATH

logger = logging.getLogger("PostBot.Database")

_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
_db = None
BANNER_CACHE: Dict[str, str] = {}

class Database:
    def __init__(self):
        self.MONGO_URL = MONGO_URL
        self.MONGO_DB_NAME = MONGO_DB_NAME

async def get_db():
    global _client, _db
    if _db is None:
        if _client is None:
            _client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
        _db = _client[MONGO_DB_NAME]
    return _db

async def close_db():
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None

async def _migrate_sqlite_if_needed():
    """Migrate data from SQLite database to MongoDB if SQLite file exists."""
    if not os.path.exists(DATABASE_PATH):
        return
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        db = await get_db()

        # Migrate users
        try:
            users = [dict(r) for r in c.execute("SELECT * FROM users").fetchall()]
            for u in users:
                await db.users.update_one({"user_id": u["user_id"]}, {"$setOnInsert": u}, upsert=True)
            if users:
                logger.info(f"SQLite -> MongoDB: Checked {len(users)} users")
        except sqlite3.OperationalError:
            pass

        # Migrate posts
        try:
            posts = [dict(r) for r in c.execute("SELECT * FROM posts").fetchall()]
            for p in posts:
                await db.posts.update_one({"post_code": p["post_code"]}, {"$setOnInsert": p}, upsert=True)
            if posts:
                logger.info(f"SQLite -> MongoDB: Checked {len(posts)} posts")
        except sqlite3.OperationalError:
            pass

        # Migrate banner_cache
        try:
            banners = [dict(r) for r in c.execute("SELECT * FROM banner_cache").fetchall()]
            for b in banners:
                await db.banner_cache.update_one({"name": b["name"]}, {"$setOnInsert": b}, upsert=True)
            if banners:
                logger.info(f"SQLite -> MongoDB: Checked {len(banners)} banners")
        except sqlite3.OperationalError:
            pass

        # Migrate user_channels
        try:
            channels = [dict(r) for r in c.execute("SELECT * FROM user_channels").fetchall()]
            for ch in channels:
                await db.user_channels.update_one(
                    {"user_id": ch["user_id"], "channel_id": str(ch["channel_id"])},
                    {"$setOnInsert": ch},
                    upsert=True
                )
            if channels:
                logger.info(f"SQLite -> MongoDB: Checked {len(channels)} channels")
        except sqlite3.OperationalError:
            pass

        conn.close()
    except Exception as e:
        logger.warning(f"SQLite migration check skipped: {e}")

async def init_db():
    global BANNER_CACHE
    db = await get_db()

    # Create MongoDB Indexes
    await db.users.create_index("user_id", unique=True)
    await db.posts.create_index("post_code", unique=True)
    await db.posts.create_index("user_id")
    await db.posts.create_index([("user_id", 1), ("created_at", -1)])
    await db.posts.create_index([("user_id", 1), ("is_favorite", 1)])
    await db.banner_cache.create_index("name", unique=True)
    await db.user_channels.create_index([("user_id", 1), ("channel_id", 1)], unique=True)

    # Automatic migration if SQLite file is present
    await _migrate_sqlite_if_needed()

    # Load banner cache from MongoDB
    cursor = db.banner_cache.find({}, {"_id": 0, "name": 1, "file_id": 1})
    async for row in cursor:
        BANNER_CACHE[row["name"]] = row["file_id"]

async def get_cached_banner_file_id(name: str) -> Optional[str]:
    return BANNER_CACHE.get(name)

async def set_cached_banner_file_id(name: str, file_id: str):
    BANNER_CACHE[name] = file_id
    db = await get_db()
    await db.banner_cache.update_one(
        {"name": name},
        {"$set": {"name": name, "file_id": file_id}},
        upsert=True
    )

async def get_or_create_user(
    user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None
) -> Tuple[Dict[str, Any], bool]:
    db = await get_db()
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if user:
        update_fields = {}
        if username and user.get("username") != username:
            update_fields["username"] = username
            user["username"] = username
        if first_name and user.get("first_name") != first_name:
            update_fields["first_name"] = first_name
            user["first_name"] = first_name
        if update_fields:
            await db.users.update_one({"user_id": user_id}, {"$set": update_fields})
        return user, False

    new_user = {
        "user_id": user_id,
        "username": username,
        "first_name": first_name or "",
        "language": "en",
        "link_preview": 0,
        "auto_save_forwards": 0,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    await db.users.update_one(
        {"user_id": user_id},
        {"$setOnInsert": new_user},
        upsert=True
    )
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return (user or new_user), True

async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    db = await get_db()
    return await db.users.find_one({"user_id": user_id}, {"_id": 0})

async def update_user_setting(user_id: int, key: str, value: Any):
    allowed_keys = {"language", "link_preview", "auto_save_forwards"}
    if key not in allowed_keys:
        return
    db = await get_db()
    await db.users.update_one({"user_id": user_id}, {"$set": {key: value}})

async def get_user_stats(user_id: int) -> Dict[str, int]:
    db = await get_db()
    posts_created = await db.posts.count_documents({"user_id": user_id})
    saved_favorites = await db.posts.count_documents({"user_id": user_id, "is_favorite": 1})
    return {
        "posts_created": posts_created,
        "saved_favorites": saved_favorites
    }

async def create_post(
    post_code: str,
    user_id: int,
    name: Optional[str],
    content_type: str,
    file_id: Optional[str],
    text: Optional[str],
    entities_json: Optional[str],
    buttons_json: Optional[str],
    text_position: str = "below"
) -> bool:
    db = await get_db()
    post_doc = {
        "post_code": post_code,
        "user_id": user_id,
        "name": name or post_code,
        "content_type": content_type,
        "file_id": file_id,
        "text": text,
        "entities_json": entities_json,
        "buttons_json": buttons_json,
        "text_position": text_position,
        "is_favorite": 0,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    await db.posts.update_one(
        {"post_code": post_code},
        {"$set": post_doc},
        upsert=True
    )
    return True

async def get_post_by_code(post_code: str) -> Optional[Dict[str, Any]]:
    db = await get_db()
    return await db.posts.find_one({"post_code": post_code}, {"_id": 0})

async def get_user_posts(user_id: int, limit: int = 5, offset: int = 0) -> List[Dict[str, Any]]:
    db = await get_db()
    cursor = db.posts.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).skip(offset).limit(limit)
    return await cursor.to_list(length=limit)

async def count_user_posts(user_id: int) -> int:
    db = await get_db()
    return await db.posts.count_documents({"user_id": user_id})

async def update_post_name(post_code: str, user_id: int, new_name: str) -> bool:
    db = await get_db()
    res = await db.posts.update_one(
        {"post_code": post_code, "user_id": user_id},
        {"$set": {"name": new_name}}
    )
    return res.modified_count > 0 or res.matched_count > 0

async def toggle_favorite(post_code: str, user_id: int) -> bool:
    db = await get_db()
    post = await db.posts.find_one({"post_code": post_code, "user_id": user_id}, {"is_favorite": 1})
    if not post:
        return False
    new_val = 0 if post.get("is_favorite") == 1 else 1
    await db.posts.update_one(
        {"post_code": post_code, "user_id": user_id},
        {"$set": {"is_favorite": new_val}}
    )
    return bool(new_val)

async def delete_post(post_code: str, user_id: int) -> bool:
    db = await get_db()
    res = await db.posts.delete_one({"post_code": post_code, "user_id": user_id})
    return res.deleted_count > 0

async def add_user_channel(user_id: int, channel_id: str, channel_title: Optional[str] = None):
    db = await get_db()
    channel_id_str = str(channel_id)
    await db.user_channels.update_one(
        {"user_id": user_id, "channel_id": channel_id_str},
        {
            "$set": {
                "user_id": user_id,
                "channel_id": channel_id_str,
                "channel_title": channel_title or channel_id_str,
                "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            }
        },
        upsert=True
    )

async def get_user_channels(user_id: int) -> List[Dict[str, Any]]:
    db = await get_db()
    cursor = db.user_channels.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).limit(6)
    return await cursor.to_list(length=6)

async def get_all_user_ids() -> List[int]:
    db = await get_db()
    cursor = db.users.find({}, {"_id": 0, "user_id": 1})
    user_ids = []
    async for doc in cursor:
        if "user_id" in doc:
            user_ids.append(doc["user_id"])
    return user_ids

async def get_total_users_count() -> int:
    db = await get_db()
    return await db.users.count_documents({})
