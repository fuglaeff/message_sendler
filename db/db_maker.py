import asyncio

from clients.models import Client
from db.base import Base, engine
from mailing_list.models import MailingList, MailingListToClients, Message


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


if __name__ == '__main__':

    asyncio.run(create_db())
