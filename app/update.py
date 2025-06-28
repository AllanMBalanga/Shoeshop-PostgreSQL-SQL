from pydantic import BaseModel, EmailStr
from typing import Literal, Optional

#PYDANTIC validators

#PUT filtering, not optional
class CustomerPut(BaseModel):
    name: str
    email: EmailStr
    password: str
    address: str

class ServiceRequestPut(BaseModel):
    total_cost: float = 0
    type: Literal["repair", "sale"]

class ProductPut(BaseModel):
    name: str
    description: str
    price: float
    stock_quantity: int = 0

class ProductVariantPut(BaseModel):
    size: str
    color: str
    stock_quantity: int = 0

class RepairPut(BaseModel):
    description: str
    status: Literal["pending", "in_progress", "completed"]

class ItemRequestPut(BaseModel):
    product_variant_id: int
    quantity: int
    unit_price: float

#PATCH filtering, optional
class CustomerPatch(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    address: Optional[str] = None

class ServiceRequestPatch(BaseModel):
    total_cost: Optional[float] = None
    type: Optional[Literal["repair", "sale"]] = None

class ProductPatch(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None

class ProductVariantPatch(BaseModel):
    size: Optional[str] = None
    color: Optional[str] = None
    stock_quantity: Optional[int] = None

class RepairPatch(BaseModel):
    description: Optional[str] = None
    status: Optional[Literal["pending", "in_progress", "completed"]] = None

class ItemRequestPatch(BaseModel):
    product_variant_id: Optional[int] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None


#for patch
def dynamic_patch_query(
        table: str, 
        data: dict, 
        table_id: int, 
        customer_id: int = None, 
        service_id: int = None, 
        product_id: int = None
        ) -> tuple[str, tuple]:
    
    set_clause = ", ".join(f"{k} = %s" for k in data)                                               # converts keys in the data dict into 'column = %s' format and joins them with commas

    if customer_id is not None:
        sql = f"UPDATE {table} SET {set_clause} WHERE id = %s AND customer_id = %s RETURNING *"     #becomes UPDATE tasks SET (name = %s, email = %s,...) WHERE id = %s AND...
        values = tuple(data.values()) + (table_id, customer_id,)                                 # returns the final SQL string and a tuple of values (dict values + record ID) for parameter substitution
    
    elif service_id is not None:
        sql = f"UPDATE {table} SET {set_clause} WHERE id = %s AND service_id = %s RETURNING *"
        values = tuple(data.values()) + (table_id, service_id)     
    
    elif product_id is not None:
        sql = f"UPDATE {table} SET {set_clause} WHERE id = %s AND product_id = %s RETURNING *" 
        values = tuple(data.values()) + (table_id, product_id,)
    
    else:
        sql = f"UPDATE {table} SET {set_clause} WHERE id = %s RETURNING *"
        values = tuple(data.values()) + (table_id,)
    
    return sql, values


