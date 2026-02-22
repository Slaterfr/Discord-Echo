import aiosqlite
import logging
from datetime import datetime
import json

DB_NAME = 'lore.db'
logger = logging.getLogger('LoreBot.Database')

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Table: users
        # Stores Discord user definition
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                discord_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table: user_aliases
        # Stores alternative names for users
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_aliases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                alias TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (discord_id)
            )
        ''')

        # Table: information
        # Connects to users by id. Stores personality, events, specific user lore.
        await db.execute('''
            CREATE TABLE IF NOT EXISTS information (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (discord_id)
            )
        ''')

        # Table: stories
        # Stores large text with lore and stories.
        # We can implement a many-to-many relation for participants later if needed,
        # but for now we'll rely on text content or metadata.
        await db.execute('''
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.commit()
        logger.info("Database initialized.")

async def upsert_user(discord_id: int, name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        # Check if user exists
        async with db.execute('SELECT name FROM users WHERE discord_id = ?', (discord_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                # Update name if changed (optional, but good for keeping track)
                if row[0] != name:
                    await db.execute('UPDATE users SET name = ? WHERE discord_id = ?', (name, discord_id))
                    await db.commit()
            else:
                await db.execute('INSERT INTO users (discord_id, name) VALUES (?, ?)', (discord_id, name))
                await db.commit()

async def add_alias(discord_id: int, alias: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT INTO user_aliases (user_id, alias) VALUES (?, ?)', (discord_id, alias))
        await db.commit()

async def add_information(discord_id: int, category: str, content: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT INTO information (user_id, category, content) VALUES (?, ?, ?)', 
                         (discord_id, category, content))
        await db.commit()

async def add_story(title: str, content: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT INTO stories (title, content) VALUES (?, ?)', (title, content))
        await db.commit()

async def get_user_profile(discord_id: int):
    """
    Fetches all data related to a user: Basic info, Aliases, and recorded Information.
    """
    profile = {}
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        
        # Basic Info
        async with db.execute('SELECT * FROM users WHERE discord_id = ?', (discord_id,)) as cursor:
            user_row = await cursor.fetchone()
            if not user_row:
                return None
            profile['name'] = user_row['name']
            profile['id'] = user_row['discord_id']

        # Aliases
        async with db.execute('SELECT alias FROM user_aliases WHERE user_id = ?', (discord_id,)) as cursor:
            aliases = await cursor.fetchall()
            profile['aliases'] = [row['alias'] for row in aliases]

        # Information
        async with db.execute('SELECT category, content FROM information WHERE user_id = ?', (discord_id,)) as cursor:
            info_rows = await cursor.fetchall()
            # Group by category
            info_data = {}
            for row in info_rows:
                cat = row['category'] or 'General'
                if cat not in info_data:
                    info_data[cat] = []
                info_data[cat].append(row['content'])
            profile['information'] = info_data
            
    return profile

async def get_recent_stories(limit=3):
    """
    Fetches the most recent stories to provide general lore context.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT title, content FROM stories ORDER BY created_at DESC LIMIT ?', (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [{'title': row['title'], 'content': row['content']} for row in rows]

async def get_all_stories():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT id, title, content, created_at FROM stories ORDER BY created_at DESC') as cursor:
            rows = await cursor.fetchall()
            return [{'id': row['id'], 'title': row['title'], 'content': row['content'], 'created_at': row['created_at']} for row in rows]
