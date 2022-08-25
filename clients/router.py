from fastapi import APIRouter, Depends, HTTPException, status

from clients.crud import ClientCrud
from clients.schemas import ClientIn, ClientOut, ClientUpdate
from db.base import get_db

clients_router = APIRouter(
    prefix='/clients',
    tags=['clients', ]
)


@clients_router.post('/',
                     response_model=ClientOut,
                     status_code=status.HTTP_201_CREATED
                     )
async def create_client(client: ClientIn, db=Depends(get_db)):
    '''
    Function for creating client. Args: pydantic model ClientIn
    and db session from async generator.
    '''
    return await ClientCrud.create(db, **client.dict())


@clients_router.get('/{id}/', response_model=ClientOut)
async def get_client(id: int, db=Depends(get_db)):
    client = await ClientCrud.get(db, id)
    if not client:
        raise HTTPException(status_code=404, detail='Client not found')
    return client


@clients_router.put('/{id}/', response_model=ClientOut)
async def update_client(id: int, client: ClientUpdate, db=Depends(get_db)):
    client_old = await ClientCrud.get(db, id)
    if not client_old:
        raise HTTPException(status_code=404, detail='Client not found')

    old_data = ClientIn(**client_old.__dict__)
    update_data = client.dict(exclude_unset=True)
    updated_item = old_data.copy(update=update_data)
    return await ClientCrud.update(db, id, **updated_item.dict())


@clients_router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(id: int, db=Depends(get_db)):
    return await ClientCrud.delete(db, id)
