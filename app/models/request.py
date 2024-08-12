from pydantic import BaseModel

class AddressRequest(BaseModel):
    addresses: list[str]
