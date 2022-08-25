from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from db.base import FilterTypes


class MailingListFilter(BaseModel):
    filter_type: FilterTypes = Field(
        description='Filter type ("tag"/"mob_code")')
    filter_value: str


class MailingListFilterOut(MailingListFilter):
    id: int


class MailingListDetail(BaseModel):
    sent: int = Field(
        description='Count clients with sent message')
    not_sent: int = Field(
        description='Count clients without sent message')
    all_clients_cnt: int = Field(
        description='Count all clients in mailing list')
    time_for_sending: int = Field(
        description='Number of seconds for sending mailing list')
    filters: List[MailingListFilter]


class MailingListBase(BaseModel):
    start_comm_timestamp: datetime
    end_comm_timestamp: datetime
    text: str


class MailingListIn(MailingListBase):
    filters: List[MailingListFilter]


class MailingListUpdate(BaseModel):
    start_comm_timestamp: Optional[datetime] = None
    end_comm_timestamp: Optional[datetime] = None
    text: Optional[str] = None


class MailingListOut(MailingListBase):
    id: int
    filters: List[MailingListFilterOut]

    class Config:
        orm_mode = True
