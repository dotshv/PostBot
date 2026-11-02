import aiosqlite
import json
from typing import Optional, List, Dict, Any, Tuple
from config import DATABASE_PATH

_db: Optional[aiosqlite.Connection] = None
BANNER_CACHE: Dict[str, str] = {}

async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DATABASE_PATH)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL;")
        await _db.execute("PRAGMA synchronous=NORMAL;")
        await _db.execute("PRAGMA temp_store=MEMORY;")
        await _db.execute("PRAGMA cache_size=10000;")
    return _db

async def close_db():
    global _db
    if _db is not None:
        await _db.close()
        _db = None

async def init_db():
    db = await get_db()
    await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            language TEXT DEFAULT 'en',
            link_preview INTEGER DEFAULT 0,
            auto_save_forwards INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_code TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            name TEXT,
            content_type TEXT NOT NULL,
            file_id TEXT,
            text TEXT,
            entities_json TEXT,
            buttons_json TEXT,
            text_position TEXT DEFAULT 'below',
            is_favorite INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS banner_cache (
            name TEXT PRIMARY KEY,
            file_id TEXT NOT NULL
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS user_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            channel_id TEXT NOT NULL,
            channel_title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, channel_id)
        )
    """)
    await db.execute("CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts (user_id)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_posts_post_code ON posts (post_code)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_user_channels ON user_channels (user_id)")
    await db.commit()

    cursor = await db.execute("SELECT name, file_id FROM banner_cache")
    rows = await cursor.fetchall()
    for row in rows:
        BANNER_CACHE[row["name"]] = row["file_id"]

async def get_cached_banner_file_id(name: str) -> Optional[str]:
    return BANNER_CACHE.get(name)

async def set_cached_banner_file_id(name: str, file_id: str):
    BANNER_CACHE[name] = file_id
    db = await get_db()
    await db.execute(
        "INSERT OR REPLACE INTO banner_cache (name, file_id) VALUES (?, ?)",
        (name, file_id)
    )
    await db.commit()

async def get_or_create_user(user_id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> Tuple[Dict[str, Any], bool]:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = await cursor.fetchone()
    if row:
        if username or first_name:
            await db.execute(
                "UPDATE users SET username = COALESCE(?, username), first_name = COALESCE(?, first_name) WHERE user_id = ?",
                (username, first_name, user_id)
            )
            await db.commit()
        return dict(row), False
    
    await db.execute(
        "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
        (user_id, username, first_name or "")
    )
    await db.commit()
    cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    new_row = await cursor.fetchone()
    return dict(new_row), True

async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None

async def update_user_setting(user_id: int, key: str, value: Any):
    allowed_keys = {"language", "link_preview", "auto_save_forwards"}
    if key not in allowed_keys:
        return
    db = await get_db()
    await db.execute(f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id))
    await db.commit()

async def get_user_stats(user_id: int) -> Dict[str, int]:
    db = await get_db()
    cursor_posts = await db.execute("SELECT COUNT(*) as cnt FROM posts WHERE user_id = ?", (user_id,))
    posts_row = await cursor_posts.fetchone()
    
    cursor_fav = await db.execute("SELECT COUNT(*) as cnt FROM posts WHERE user_id = ? AND is_favorite = 1", (user_id,))
    fav_row = await cursor_fav.fetchone()
    
    return {
        "posts_created": posts_row["cnt"] if posts_row else 0,
        "saved_favorites": fav_row["cnt"] if fav_row else 0
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
    await db.execute("""
        INSERT INTO posts (
            post_code, user_id, name, content_type, file_id, text, entities_json, buttons_json, text_position
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        post_code, user_id, name or post_code, content_type, file_id, text, entities_json, buttons_json, text_position
    ))
    await db.commit()
    return True

async def get_post_by_code(post_code: str) -> Optional[Dict[str, Any]]:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM posts WHERE post_code = ?", (post_code,))
    row = await cursor.fetchone()
    return dict(row) if row else None

async def get_user_posts(user_id: int, limit: int = 5, offset: int = 0) -> List[Dict[str, Any]]:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM posts WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (user_id, limit, offset)
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]

async def count_user_posts(user_id: int) -> int:
    db = await get_db()
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM posts WHERE user_id = ?", (user_id,))
    row = await cursor.fetchone()
    return row["cnt"] if row else 0

async def update_post_name(post_code: str, user_id: int, new_name: str) -> bool:
    db = await get_db()
    cursor = await db.execute(
        "UPDATE posts SET name = ? WHERE post_code = ? AND user_id = ?",
        (new_name, post_code, user_id)
    )
    await db.commit()
    return cursor.rowcount > 0

async def toggle_favorite(post_code: str, user_id: int) -> bool:
    db = await get_db()
    cursor = await db.execute(
        "SELECT is_favorite FROM posts WHERE post_code = ? AND user_id = ?",
        (post_code, user_id)
    )
    row = await cursor.fetchone()
    if not row:
        return False
    new_val = 0 if row["is_favorite"] == 1 else 1
    await db.execute(
        "UPDATE posts SET is_favorite = ? WHERE post_code = ? AND user_id = ?",
        (new_val, post_code, user_id)
    )
    await db.commit()
    return bool(new_val)

async def delete_post(post_code: str, user_id: int) -> bool:
    db = await get_db()
    cursor = await db.execute(
        "DELETE FROM posts WHERE post_code = ? AND user_id = ?",
        (post_code, user_id)
    )
    await db.commit()
    return cursor.rowcount > 0

async def add_user_channel(user_id: int, channel_id: str, channel_title: Optional[str] = None):
    db = await get_db()
    await db.execute("""
        INSERT OR REPLACE INTO user_channels (user_id, channel_id, channel_title)
        VALUES (?, ?, ?)
    """, (user_id, channel_id, channel_title or channel_id))
    await db.commit()

async def get_user_channels(user_id: int) -> List[Dict[str, Any]]:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM user_channels WHERE user_id = ? ORDER BY created_at DESC LIMIT 6",
        (user_id,)
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]

async def get_all_user_ids() -> List[int]:
    db = await get_db()
    cursor = await db.execute("SELECT user_id FROM users")
    rows = await cursor.fetchall()
    return [r["user_id"] for r in rows]

async def get_total_users_count() -> int:
    db = await get_db()
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM users")
    row = await cursor.fetchone()
    return row["cnt"] if row else 0
