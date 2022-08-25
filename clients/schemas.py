import re
from typing import Optional

from pydantic import BaseModel, Field, validator


class ClientIn(BaseModel):
    mob_number: int
    mob_code: int
    tag: str = Field(max_length=10)
    time_zone: int = Field(ge=-12, le=12)

    @validator('mob_number')
    def mob_number_validator(cls, mob_number: int):
        mob_number_str = str(mob_number)

        if len(mob_number_str) != 11:
            raise ValueError('Mob number length must equals 11')

        if not re.search(r'^7[0-9]{10}$', mob_number_str):
            raise ValueError('Mob number must start with 7')

        return mob_number

    @validator('mob_code')
    def mob_code_validator(cls, mob_code: int):
        if len(str(mob_code)) != 3:
            raise ValueError('Mob code length must equals 3')

        return mob_code


class ClientUpdate(BaseModel):
    mob_number: Optional[int] = None
    mob_code: Optional[int] = None
    tag: Optional[str] = Field(default=None, max_length=10)
    time_zone: Optional[int] = Field(default=None, ge=-12, le=12)


class ClientOut(ClientIn):
    id: int

    class Config:
        orm_mode = True
