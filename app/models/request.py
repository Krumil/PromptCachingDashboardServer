from pydantic import BaseModel

class AddressRequest(BaseModel):
    address: str
