import aiosqlite
from aiogram import types
from app.config import DB_NAME

async def create_tables():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state 
        (user_id INTEGER PRIMARY KEY, question_index INTEGER, score INTEGER DEFAULT 0)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS leaderboard 
         (user_id INTEGER PRIMARY KEY, username TEXT, score INTEGER)''')
        await db.commit()

async def update_quiz_index(user_id, index):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT user_id FROM quiz_state WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            exists = await cursor.fetchone()
            
        if exists:
            await db.execute(
                "UPDATE quiz_state SET question_index = ? WHERE user_id = ?",
                (index, user_id)
            )
        else:
            await db.execute(
                "INSERT INTO quiz_state (user_id, question_index, score) VALUES (?, ?, 0)",
                (user_id, index)
            )
        await db.commit()

async def get_quiz_index(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            'SELECT question_index FROM quiz_state WHERE user_id = (?)',
            (user_id,)
        ) as cursor:
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0
            
async def get_user_score(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT score FROM quiz_state WHERE user_id = ?", 
            (user_id,)
        ) as cursor:
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0

async def update_user_score(user_id, score, username=None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE quiz_state SET score = ? WHERE user_id = ?",
            (score, user_id)
        )
        if username:
            await db.execute(
                '''INSERT OR REPLACE INTO leaderboard (user_id, username, score)
                   VALUES (?, ?, ?)''',
                (user_id, username, score)
            )
        await db.commit()          
            
async def update_leaderboard(user_id, username, score):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''INSERT OR REPLACE INTO leaderboard (user_id, username, score)
                            VALUES (?, ?, ?)''', (user_id, username, score))
        await db.commit()

async def show_leaderboard(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('''SELECT username, score FROM leaderboard
                                 ORDER BY score DESC LIMIT 5''') as cursor:
            tops = await cursor.fetchall()

    leaderboard_message = "🥇🥈🥉 Leaderboard:\n"
    for i, (username, score) in enumerate(tops, start=1):
        leaderboard_message += f"{i}. {username}: {score} scores\n"

    await message.answer(leaderboard_message)            