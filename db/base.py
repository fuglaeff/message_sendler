from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

engine = create_async_engine(
    'sqlite+aiosqlite:///test_task_work.db')

DBSession: AsyncSession = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False)


class FilterTypes(Enum):
    tag: str = 'tag'
    mob_code: str = 'mob_code'


class SentStatus(Enum):
    sent: str = 'sent'
    no_sent: str = 'no_sent'


async def get_db():
    db: AsyncSession = DBSession()
    try:
        yield db
    finally:
        await db.close()
