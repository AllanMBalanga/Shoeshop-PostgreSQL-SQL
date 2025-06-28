from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal, List
from datetime import datetime

#PYDANTIC validators

#Base response models
class BaseCustomerResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    address: str
    created_at: datetime

    class Config:
        orm_mode = True

class BaseServiceResponse(BaseModel):
    id: int
    customer_id: int
    total_cost: float
    date: datetime
    type: Literal["sale","repair"]

    class Config:
        orm_mode = True


class BaseProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    stock_quantity: int
    created_at: datetime

    class Config:
        orm_mode = True

class BaseProductVariantResponse(BaseModel):
    id: int
    product_id: int
    size: str
    color: str
    stock_quantity: int

    class Config:
        orm_mode = True

class BaseRepairResponse(BaseModel):
    id: int
    service_id: int
    description: str
    status: Literal["pending", "in_progress", "completed"]
    created_at: datetime
    start_date: Optional[datetime] = None
    finished_date: Optional[datetime] = None

    class Config:
        orm_mode = True

class BaseItemRequestResponse(BaseModel):
    id: int
    service_id: int
    product_variant_id: int
    quantity: int
    unit_price: float
    created_at: datetime

    class Config:
        orm_mode = True


#Response model filtering
class CustomerResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    address: str
    created_at: datetime
    services: List[BaseServiceResponse] = Field(default_factory=list)

    class Config:
        orm_mode = True

class ServiceResponse(BaseModel):
    id: int
    customer_id: int
    type: Literal["sale","repair"]
    total_cost: Optional[float] = 0
    date: datetime
    user: CustomerResponse  #uses Customer Response as a response model
    repairs: Optional[List[BaseRepairResponse]] = Field(default_factory=list)
    items: Optional[List[BaseItemRequestResponse]] = Field(default_factory=list)

    class Config:
        orm_mode = True

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    stock_quantity: int
    created_at: datetime
    variants: Optional[List[BaseProductVariantResponse]] = Field(default_factory=list)

    class Config:
        orm_mode = True

class ProductVariantResponse(BaseModel):
    id: int
    product_id: int
    size: str
    color: str
    stock_quantity: int
    product: BaseProductResponse    #uses BaseProductResponse as a response model

    class Config:
        orm_mode = True

class RepairResponse(BaseModel):
    id: int
    service_id: int
    description: str
    status: Literal["pending", "in_progress", "completed"]
    created_at: datetime
    start_date: Optional[datetime] = None
    finished_date: Optional[datetime] = None
    service: BaseServiceResponse    #uses BaseServiceResponse as a response model

    class Config:
        orm_mode = True

class ItemRequestResponse(BaseModel):
    id: int
    service_id: int
    product_variant_id: int
    quantity: int
    unit_price: float
    created_at: datetime
    service: BaseServiceResponse    #uses BaseServiceResponse as a response model

    class Config:
        orm_mode = True