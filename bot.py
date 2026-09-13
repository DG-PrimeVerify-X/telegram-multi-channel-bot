import asyncio
from database.models import init_db

async def main():
    await init_db()
    print("Database initialized. Bot GUI modules will be enabled next.")

if __name__ == "__main__":
    asyncio.run(main())
