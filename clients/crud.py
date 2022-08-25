from sqlalchemy.sql import update

from clients.models import Client
from db.base import AsyncSession
from db.mixins import Crud


class ClientCrud(Crud):

    @staticmethod
    async def create(db: AsyncSession, **kwargs):
        client = Client(**kwargs)
        db.add(client)
        await db.commit()
        return client

    @staticmethod
    async def get(db: AsyncSession, id: int):
        return await db.get(Client, id)

    @staticmethod
    async def delete(db: AsyncSession, id: int):
        el = await db.get(Client, id)
        await db.delete(el)
        await db.commit()

    @staticmethod
    async def update(db: AsyncSession, id: int, **kwargs):
        stmt = (
            update(Client).
            where(Client.id == id).
            values(**kwargs)
        )

        await db.execute(stmt)
        await db.commit()
        return await ClientCrud.get(db, id)
