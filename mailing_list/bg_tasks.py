import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict

import aiohttp

from db.base import AsyncSession, DBSession
from mailing_list.crud import MailingListCrud, MessageUpdate

headers = {
    'Authorization': f'Bearer {os.getenv("SEND_TOKEN")}',
    'Content-Type': 'application/json'
}


async def message_sendler(
        msg: Dict[str, Any], text: str, session: aiohttp.ClientSession) -> int:
    data = {
        'id': msg.get('id'),
        'phone': msg.get('mob_number'),
        'text': text
    }

    json_data = json.dumps(data)
    async with session.post(
        f'{os.getenv("SEND_API_URL")}{msg.get("message_id")}',
        data=json_data,
        headers=headers
    ) as response:
        status = response.status

    return status


async def do_mailing_list(
        text: str, mailing_list_id: int, db: AsyncSession) -> None:
    msg = await MessageUpdate.get_msg_for_sending(db, mailing_list_id)
    async with aiohttp.ClientSession() as session:
        while msg:
            result = await message_sendler(msg, text, session)
            if result == 200:
                await MessageUpdate.update(
                    db, id=msg.get('message_id'), time=datetime.utcnow())

            msg = await MessageUpdate.get_msg_for_sending(
                db, mailing_list_id, except_client_id=msg.get('id'))


async def bg_mailing(mailing_list: Dict[str, Any]) -> None:
    mailing_list['start_comm_timestamp'] = (
        mailing_list['start_comm_timestamp'].replace(tzinfo=None))
    time_start = mailing_list.get('start_comm_timestamp')
    time_sleep = time_start.replace(tzinfo=None) - datetime.utcnow()
    if datetime.utcnow() < time_start.replace(tzinfo=None):
        await asyncio.sleep(time_sleep.seconds)

    async with DBSession() as db:
        mailing_list_db = await MailingListCrud.get(db, mailing_list.get('id'))
        start_condition = (mailing_list.get('start_comm_timestamp')
                           == mailing_list_db.get('start_comm_timestamp'))
        if start_condition:
            await do_mailing_list(
                mailing_list.get('text'), mailing_list.get('id'), db)
