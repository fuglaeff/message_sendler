from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.sql import and_, between, case, delete, func, or_, select, update

from clients.models import Client
from db.base import AsyncSession, FilterTypes, SentStatus
from db.mixins import Crud
from mailing_list.models import MailingList, MailingListToClients, Message


class MailingListCrud(Crud):

    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> Dict[str, Any]:
        filters: List[Dict[str, Union[str, int]]] = kwargs.pop('filters')
        mailing_list = MailingList(**kwargs)

        db.add(mailing_list)
        await db.commit()

        tags_codes_add = []
        for filter in filters:
            mailing_list_to_user = MailingListToClients(
                mailing_list_id=mailing_list.id,
                filter_type=filter.get('filter_type'),
                filter_value=filter.get('filter_value')
            )

            tags_codes_add.append(mailing_list_to_user)

        db.add_all(tags_codes_add)

        await db.commit()

        filters_db = await mailing_list.filters

        await mailing_list.create_msgs()

        return {**mailing_list.__dict__, 'filters': filters_db}

    @staticmethod
    async def get(db: AsyncSession, id: int) -> Dict[str, Any]:
        stmt = (
            select(MailingList).
            where(MailingList.id == id)
        )
        mailing_list = (await db.execute(stmt)).scalar()
        if not mailing_list:
            raise ValueError('Mailing List doesn\'t exists.')
        filters = await mailing_list.filters
        return {**mailing_list.__dict__, 'filters': filters}

    @staticmethod
    async def delete(db: AsyncSession, id: int) -> None:
        el = await db.get(MailingList, id)
        await db.delete(el)
        await db.commit()

    @staticmethod
    async def update(db: AsyncSession, id: int, **kwargs) -> Dict[str, Any]:
        stmt = (
            update(MailingList).
            where(MailingList.id == id).
            values(**kwargs)
        )
        await db.execute(stmt)
        await db.commit()
        return await MailingListCrud.get(db, id)

    @staticmethod
    async def get_by_filter_id(
            db: AsyncSession, filter_id: int) -> Dict[str, Any]:
        stmt = (
            select(MailingList).
            join(MailingListToClients).
            where(MailingListToClients.id == filter_id)
        )
        mailing_list = (await db.execute(stmt)).scalar()
        if not mailing_list:
            raise ValueError('Filter doesn\'t exists.')
        filters = await mailing_list.filters
        return {**mailing_list.__dict__, 'filters': filters}

    @staticmethod
    async def update_filter(
                db: AsyncSession,
                filter_id: int,
                mailing_list_id: int,
                **kwargs
            ) -> Dict[str, Any]:
        tag_condition = and_(
            MailingListToClients.filter_type == FilterTypes.tag,
            MailingListToClients.filter_value == Client.tag
        )
        mob_code_condition = and_(
            MailingListToClients.filter_type == FilterTypes.mob_code,
            MailingListToClients.filter_value == Client.mob_code
        )

        old_filter_clients = (
            select(Client.id).
            join(MailingListToClients, or_(tag_condition, mob_code_condition)).
            where(
                MailingListToClients.mailing_list_id == mailing_list_id,
                MailingListToClients.id == filter_id,
            ).
            distinct()
        )

        deleting_old_clients = (
            delete(Message).
            where(
                Message.client_id.in_(old_filter_clients),
                Message.status == SentStatus.no_sent
            )
        )

        await db.execute(deleting_old_clients)
        await db.commit()

        stmt = (
            update(MailingListToClients).
            where(MailingListToClients.id == filter_id).
            values(**kwargs)
        )

        await db.execute(stmt)
        await db.commit()

        existing_clients = (
            select(Message.client_id).
            where(Message.mailing_list_id == mailing_list_id)
        )

        new_filter_clients = (
            select(Client.id).
            join(MailingListToClients, or_(tag_condition, mob_code_condition)).
            where(
                MailingListToClients.mailing_list_id == mailing_list_id,
                MailingListToClients.id == filter_id,
                Client.id.not_in(existing_clients)
            ).
            distinct()
        )

        mailing_list_clients = await db.stream(new_filter_clients)
        date_add = datetime.utcnow()

        async for client in mailing_list_clients:
            msg = Message(
                sent_time=date_add,
                mailing_list_id=mailing_list_id,
                client_id=client[0]
            )

            db.add(msg)
            await db.commit()

        return await MailingListCrud.get_by_filter_id(db, filter_id)


class MessageUpdate:

    @staticmethod
    async def update(db: AsyncSession,
                     id: int,
                     time: datetime,
                     status: SentStatus = SentStatus.sent
                     ) -> None:
        stmt = (
            update(Message).
            where(Message.id == id).
            values(sent_time=time, status=status)
        )

        await db.execute(stmt)
        await db.commit()

    @staticmethod
    async def get_msg_for_sending(
            db: AsyncSession,
            mailing_list_id: int,
            except_client_id: Optional[int] = None
            ) -> Optional[Dict[str, Any]]:
        time_condition = (
            between(
                Client.time_zone,
                (func.julianday(MailingList.start_comm_timestamp)
                 - func.julianday(func.now())) * 24,
                (func.julianday(MailingList.end_comm_timestamp)
                 - func.julianday(func.now())) * 24)
        )

        stmt = (
            select(
                Client.id,
                Client.mob_number,
                Message.id.label('message_id')
            ).
            join(Client).
            join(MailingList).
            where(
                Message.status == SentStatus.no_sent,
                time_condition,
                Message.mailing_list_id == mailing_list_id,
                Message.client_id != except_client_id,
                MailingList.end_comm_timestamp >= func.now()
            ).
            order_by(func.random())
        )

        row = (await db.execute(stmt)).first()
        return row._asdict() if row else row


async def statistic(id: int, db: AsyncSession):
    stmt = (
        select(
            func.count(
                case(
                    (Message.status == SentStatus.no_sent, Message.client_id),
                    else_=None
                )
            ).label('not_sent'),
            func.count(
                case(
                    (Message.status == SentStatus.sent, Message.client_id),
                    else_=None
                )
            ).label('sent'),
            func.count(Message.client_id).label('all_clients_cnt'),
            (
                (func.julianday(func.max(Message.sent_time))
                 - func.julianday(func.min(Message.sent_time))
                 ) * 24 * 3600
            ).label('time_for_sending')
        ).
        where(Message.mailing_list_id == id)
    )

    row = (await db.execute(stmt)).first()
    if not row:
        raise ValueError('Mailing List doesn\'t exist')

    mailing_list = await db.get(MailingList, id)
    filters = await mailing_list.filters
    return {**row._asdict(), 'filters': filters}
