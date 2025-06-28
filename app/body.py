from pydantic import BaseModel, EmailStr
from typing import Literal, Optional

#PYDANTIC validators

#Schema for inserting data
class Customer(BaseModel):
    name: str
    email: EmailStr
    password: str
    address: str

class ServiceRequest(BaseModel):
    total_cost: Optional[float] = 0
    type: Literal["repair","sale"]

class Product(BaseModel):
    name: str
    description: str
    price: float
    stock_quantity: int

class ProductVariant(BaseModel):
    size: str
    color: str
    stock_quantity: int

class Repair(BaseModel):
    description: str
    status: Literal["pending", "in_progress", "completed"]

class ItemRequest(BaseModel):
    product_variant_id: int
    quantity: int
    unit_price: float


#Token
class Token(BaseModel):
    access_token: str
    token_type: str
    customer_id: int
   
class TokenData(BaseModel):
    id: Optional[int] = None