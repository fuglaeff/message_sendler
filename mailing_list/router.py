from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from db.base import get_db
from mailing_list.bg_tasks import bg_mailing
from mailing_list.crud import MailingListCrud, statistic
from mailing_list.schemas import (MailingListDetail, MailingListFilter, MailingListIn,
                                  MailingListOut, MailingListUpdate)

mailing_list_router = APIRouter(
    prefix='/mailing-list',
    tags=['mailing-list', ]
)


@mailing_list_router.post('/',
                          response_model=MailingListOut,
                          status_code=status.HTTP_201_CREATED
                          )
async def create_mailing_list(
            mailing_list: MailingListIn,
            background_task: BackgroundTasks,
            db=Depends(get_db)
        ):
    mailing_list_from_db = await MailingListCrud.create(
        db, **mailing_list.dict())
    background_task.add_task(bg_mailing, mailing_list_from_db)
    return mailing_list_from_db


@mailing_list_router.get('/{id}/', response_model=MailingListOut)
async def get_mailing_list(id: int, db=Depends(get_db)):
    try:
        return await MailingListCrud.get(db, id)
    except ValueError:
        raise HTTPException(status_code=404, detail='Mailing List not found')


@mailing_list_router.put('/{id}/', response_model=MailingListOut)
async def update_mailing_list(
            id: int,
            mailing_list: MailingListUpdate,
            background_task: BackgroundTasks,
            db=Depends(get_db)
        ):
    mailing_list_old = await MailingListCrud.get(db, id)
    if not mailing_list_old:
        raise HTTPException(status_code=404, detail='Mailing List not found')

    old_data = MailingListUpdate(**mailing_list_old)
    update_mailing_list = mailing_list.dict(exclude_unset=True)
    updated_mailing_list = old_data.copy(update=update_mailing_list)
    update_mailing_list_from_db = await MailingListCrud.update(
        db, id, **updated_mailing_list.dict())
    new_dg_task_condition = (updated_mailing_list.start_comm_timestamp
                             .replace(tzinfo=None)
                             != mailing_list_old.get('start_comm_timestamp'))
    if new_dg_task_condition:
        background_task.add_task(bg_mailing, update_mailing_list_from_db)
    return update_mailing_list_from_db


@mailing_list_router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_mailing_list(id: int, db=Depends(get_db)):
    return await MailingListCrud.delete(db, id)


@mailing_list_router.put(
    '/{mailing_list_id}/filter/{filter_id}/', tags=['filter', ])
async def update_mailing_list_filter(
            mailing_list_id: int,
            filter_id: int,
            filter_: MailingListFilter,
            db=Depends(get_db)
        ):
    try:
        return await MailingListCrud.update_filter(
            db, filter_id, mailing_list_id, **filter_.dict())
    except ValueError:
        raise HTTPException(status_code=404, detail='Filter not found')


@mailing_list_router.get('/statistic/{id}', response_model=MailingListDetail)
async def statistic_handler(id: int, db=Depends(get_db)):
    return await statistic(id, db)
