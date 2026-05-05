import aiosqlite

DB_NAME = "transactions.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,       
                user_id INTEGER,                            
                category TEXT,                            
                amount REAL,                               
                date TEXT                                  
            )
        """)
        await db.commit()