from fastapi import FastAPI

from clients.router import clients_router
from mailing_list.router import mailing_list_router

app = FastAPI()

app.include_router(router=clients_router)
app.include_router(router=mailing_list_router)
