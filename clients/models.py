from sqlalchemy import Column, Integer, String

from db.base import Base


class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True)
    mob_number = Column(Integer, nullable=False)
    mob_code = Column(String(3), nullable=False)
    tag = Column(String(10))
    time_zone = Column(Integer, nullable=False)
