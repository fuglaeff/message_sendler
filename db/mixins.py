from abc import ABC, abstractmethod

from db.base import AsyncSession


class Crud(ABC):

    @staticmethod
    @abstractmethod
    async def create(db: AsyncSession, **kwargs):
        pass

    @staticmethod
    @abstractmethod
    async def get(db: AsyncSession, id: int):
        pass

    @staticmethod
    @abstractmethod
    async def delete(db: AsyncSession, id: int):
        pass

    @staticmethod
    @abstractmethod
    async def update(db: AsyncSession, id: int, **kwargs):
        pass
