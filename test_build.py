import asyncio
from database.models import init_db
from database.queries import DB

async def main():
    path="data/test_build.db"
    await init_db(path)
    db=DB(path)
    await db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)",("build_test","ok"))
    row=await db.fetchone("SELECT value FROM settings WHERE key=?",("build_test",))
    assert row["value"]=="ok"
    print("BUILD TEST OK")
if __name__=="__main__":
    asyncio.run(main())
