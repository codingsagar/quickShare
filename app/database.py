from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
import asyncio

DATABASE_URL = "sqlite:///./database.db"  

engine = create_async_engine(DATABASE_URL, echo=True)

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

asyncio.run(create_db_and_tables())
