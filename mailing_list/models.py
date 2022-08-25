from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.sql import and_, or_, select

from clients.models import Client
from db.base import Base, DBSession, FilterTypes, SentStatus


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    sent_time = Column(DateTime)
    status = Column(Enum(SentStatus), default=SentStatus.no_sent)
    mailing_list_id = Column(Integer, ForeignKey('mailing_list.id'))
    client_id = Column(Integer, ForeignKey('clients.id'))


class MailingListToClients(Base):
    __tablename__ = 'mailing_list_to_clients'

    id = Column(Integer, primary_key=True)
    mailing_list_id = Column(Integer, ForeignKey('mailing_list.id'))
    filter_type = Column(Enum(FilterTypes))
    filter_value = Column(String)


class MailingList(Base):
    __tablename__ = 'mailing_list'

    id = Column(Integer, primary_key=True)
    start_comm_timestamp = Column(DateTime)
    text = Column(String(300))
    end_comm_timestamp = Column(DateTime)

    async def create_msgs(self) -> None:
        tag_condition = and_(
            MailingListToClients.filter_type == FilterTypes.tag,
            MailingListToClients.filter_value == Client.tag
        )
        mob_code_condition = and_(
            MailingListToClients.filter_type == FilterTypes.mob_code,
            MailingListToClients.filter_value == Client.mob_code
        )

        stmt = (
            select(Client.id).
            join(MailingListToClients, or_(tag_condition, mob_code_condition)).
            where(MailingListToClients.mailing_list_id == self.id).
            distinct()
        )

        async with DBSession() as db:
            mailing_list_clients = await db.stream(stmt)
            date_add = datetime.utcnow()

            async for client in mailing_list_clients:
                msg = Message(
                    sent_time=date_add,
                    mailing_list_id=self.id,
                    client_id=client[0]
                )

                db.add(msg)
                await db.commit()

    @property
    async def filters(self) -> List[Dict[str, Any]]:
        stmt = (
            select(
                MailingListToClients.id,
                MailingListToClients.filter_type,
                MailingListToClients.filter_value
            ).
            where(MailingListToClients.mailing_list_id == self.id)
        )

        async with DBSession() as db:
            filters = await db.execute(stmt)

        return [filter._asdict() for filter in filters]
