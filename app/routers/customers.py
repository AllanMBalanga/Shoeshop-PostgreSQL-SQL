from ..database import Database
from fastapi import APIRouter, status, Depends, HTTPException
from ..body import Customer, TokenData
from ..update import CustomerPut, CustomerPatch, dynamic_patch_query
from ..response import CustomerResponse
from typing import List
from ..status_code import validate_customer_exists, exception, validate_customer_ownership
from ..utils import hash
from ..oauth2 import get_current_user
from ..relationships import customer_relationship

router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)

db = Database()

@router.get("/", response_model=List[CustomerResponse])
def get_customers():
    db.cursor.execute("SELECT * FROM customers")
    customers = db.cursor.fetchall()
    
    return [customer_relationship(customer, db) for customer in customers]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=CustomerResponse)
def create_customer(customer:Customer):
    try:
        customer.password = hash(customer.password)
        db.cursor.execute(
            "INSERT INTO customers (name, email, password, address) VALUES (%s, %s, %s, %s) RETURNING *", 
            tuple(customer.dict().values())
            )
        new_customer = db.cursor.fetchone()

        db.conn.commit()
        return new_customer
    
    except Exception as e:
        db.conn.rollback()
        exception(e)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id:int):
    db.cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
    customer = db.cursor.fetchone()
    validate_customer_exists(customer, customer_id)

    return customer_relationship(customer, db)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_custoemr(customer_id: int, current_user: TokenData = Depends(get_current_user)):
    try:
        db.cursor.execute(
            "DELETE FROM customers WHERE id = %s RETURNING *", (customer_id,)
        )
        customer = db.cursor.fetchone()
        validate_customer_exists(customer, customer_id)
        validate_customer_ownership(customer["id"], current_user.id)

        db.conn.commit()
        return

    #raises the errors captured from status_code.py
    except HTTPException as http_error:
        raise http_error
    
    #if not from status_code.py, rollback DB and logs
    except Exception as e:
        db.conn.rollback()
        exception(e)


@router.put("/{customer_id}", response_model=CustomerResponse)
def put_customer(customer_id: int, customer: CustomerPut, current_user: TokenData = Depends(get_current_user)):
    try:
        customer.password = hash(customer.password)
        db.cursor.execute(
            "UPDATE customers SET name = %s, email = %s, password = %s, address = %s WHERE id = %s RETURNING *" ,
            (tuple(customer.dict().values()) + (customer_id,))
            )
        updated_customer = db.cursor.fetchone()
        validate_customer_exists(updated_customer, customer_id)
        validate_customer_ownership(updated_customer["id"], current_user.id)

        db.conn.commit()
        return customer_relationship(updated_customer, db)
    
    except HTTPException as http_error:
        raise http_error
    
    except Exception as e:
        db.conn.rollback()
        exception(e)


@router.patch("/{customer_id}", response_model=CustomerResponse)
def patch_customer(customer_id: int, customer: CustomerPatch, current_user: TokenData = Depends(get_current_user)):
    try:
        customer.password = hash(customer.password)
        sql, values = dynamic_patch_query("customers", customer.dict(exclude_unset=True), table_id=customer_id)
        db.cursor.execute(sql, values)
        updated_customer = db.cursor.fetchone()
        validate_customer_exists(updated_customer, customer_id)
        validate_customer_ownership(updated_customer["id"], current_user.id)

        db.conn.commit()
        return customer_relationship(updated_customer, db)
    
    except HTTPException as http_error:
        raise http_error
    
    except Exception as e:
        db.conn.rollback()
        exception(e)

