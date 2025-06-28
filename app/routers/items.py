from fastapi import APIRouter, status, HTTPException, Depends
from ..body import ItemRequest, TokenData
from ..response import ItemRequestResponse
from ..update import ItemRequestPatch, ItemRequestPut, dynamic_patch_query
from ..database import Database
from typing import List
from ..status_code import validate_variant_exists, validate_service_type, validate_service_exists, validate_customer_exists, validate_item_request_exists, exception, validate_customer_ownership
from ..oauth2 import get_current_user
from ..relationships import type_of_service_relationship

router = APIRouter(
    prefix="/customers/{customer_id}/services/{service_id}/items",
    tags=["Item Requests"]
)

db = Database()


@router.get("/", response_model=List[ItemRequestResponse])
def get_item_requests(customer_id: int, service_id: int):
    db.cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
    customer = db.cursor.fetchone()
    validate_customer_exists(customer, customer_id)

    db.cursor.execute("SELECT * FROM service_requests WHERE id = %s AND customer_id = %s", (service_id, customer_id))
    service = db.cursor.fetchone()
    validate_service_exists(service, service_id)
    validate_service_type(service, "sale")

    db.cursor.execute("SELECT * FROM item_requests WHERE service_id = %s", (service_id,))
    item_requests = db.cursor.fetchall()

    return [type_of_service_relationship(item_request, db) for item_request in item_requests]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ItemRequestResponse)
def create_item_request(customer_id: int, service_id: int, item: ItemRequest, current_user: TokenData = Depends(get_current_user)):
    try:
        db.cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = db.cursor.fetchone()
        validate_customer_exists(customer, customer_id)

        db.cursor.execute("SELECT * FROM service_requests WHERE id = %s AND customer_id = %s", (service_id, customer_id))
        service = db.cursor.fetchone()
        validate_service_exists(service, service_id)
        validate_service_type(service, "sale")
        validate_customer_ownership(service["customer_id"], current_user.id)

        db.cursor.execute("SELECT * FROM product_variants WHERE id = %s", (item.product_variant_id,))
        product_variant = db.cursor.fetchone()
        validate_variant_exists(product_variant, item.product_variant_id)

        item_request_data = item.dict()
        item_request_data["service_id"] = service_id

        db.cursor.execute(
            "INSERT INTO item_requests (product_variant_id, quantity, unit_price, service_id) VALUES (%s, %s, %s, %s) RETURNING *", 
            tuple(item_request_data.values())
            )
        created_item_request = db.cursor.fetchone()

        db.conn.commit()
        return type_of_service_relationship(created_item_request, db)
    
    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        db.conn.rollback()
        exception(e)


@router.get("/{item_id}", response_model=ItemRequestResponse)
def get_item_by_id(customer_id: int, service_id: int, item_id: int):
    db.cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
    customer = db.cursor.fetchone()
    validate_customer_exists(customer, customer_id)
    
    db.cursor.execute("SELECT * FROM service_requests WHERE id = %s AND customer_id = %s", (service_id, customer_id))
    service = db.cursor.fetchone()
    validate_service_exists(service, service_id)
    validate_service_type(service, "sale")

    db.cursor.execute("SELECT * FROM item_requests WHERE id = %s AND service_id = %s", (item_id, service_id))
    item_request = db.cursor.fetchone()
    validate_item_request_exists(item_request, item_id)

    return type_of_service_relationship(item_request, db)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item_request(customer_id: int, service_id: int, item_id: int, current_user: TokenData = Depends(get_current_user)):
    try:
        db.cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = db.cursor.fetchone()
        validate_customer_exists(customer, customer_id)
        
        db.cursor.execute("SELECT * FROM service_requests WHERE id = %s AND customer_id = %s", (service_id, customer_id))
        service = db.cursor.fetchone()
        validate_service_exists(service, service_id)
        validate_service_type(service, "sale")
        validate_customer_ownership(service["customer_id"], current_user.id)

        db.cursor.execute("DELETE FROM item_requests WHERE id = %s AND service_id = %s RETURNING *", (item_id, service_id))
        item_request = db.cursor.fetchone()
        validate_item_request_exists(item_request, item_id)
        
        db.conn.commit()
        return
    
    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        db.conn.rollback()
        exception(e)
    

@router.put("/{item_id}", response_model=ItemRequestResponse)
def put_item_request(customer_id: int, service_id: int, item_id: int, item: ItemRequestPut, current_user: TokenData = Depends(get_current_user)):
    try:
        db.cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = db.cursor.fetchone()
        validate_customer_exists(customer, customer_id)
        
        db.cursor.execute("SELECT * FROM service_requests WHERE id = %s AND customer_id = %s", (service_id, customer_id))
        service = db.cursor.fetchone()
        validate_service_exists(service, service_id)
        validate_service_type(service, "sale")
        validate_customer_ownership(service["customer_id"], current_user.id)

        db.cursor.execute("SELECT * FROM item_requests WHERE id = %s AND service_id = %s", (item_id, service_id))
        existing_item = db.cursor.fetchone()
        validate_item_request_exists(existing_item, item_id)

        update_data = item.dict()

        # Prevent product_variant_id updates
        if "product_variant_id" in update_data:
            if update_data["product_variant_id"] != existing_item["product_variant_id"]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product variant cannot be changed after creation")
            update_data.pop("product_variant_id")

        def dynamic_patch_query(table: str, data: dict, table_id: int, service_id: int) -> tuple[str, tuple]:
            set_clause = ", ".join(f"{k} = %s" for k in data)                      
            sql = f"UPDATE {table} SET {set_clause} WHERE id = %s AND service_id = %s RETURNING *"     
            return sql, tuple(data.values()) + (table_id, service_id)         
        
        sql, values = dynamic_patch_query("item_requests", data=item.dict(exclude_unset=True), table_id=item_id, service_id=service_id)
        db.cursor.execute(sql, values)
        updated_item_request = db.cursor.fetchone()
        
        db.conn.commit()
        return type_of_service_relationship(updated_item_request, db)
    
    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        db.conn.rollback()
        exception(e)


@router.patch("/{item_id}", response_model=ItemRequestResponse)
def put_item_request(customer_id: int, service_id: int, item_id: int, item: ItemRequestPatch, current_user: TokenData = Depends(get_current_user)):
    try:
        db.cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = db.cursor.fetchone()
        validate_customer_exists(customer, customer_id)
        
        db.cursor.execute("SELECT * FROM service_requests WHERE id = %s AND customer_id = %s", (service_id, customer_id))
        service = db.cursor.fetchone()
        validate_service_exists(service, service_id)
        validate_service_type(service, "sale")
        validate_customer_ownership(service["customer_id"], current_user.id)

        db.cursor.execute("SELECT * FROM item_requests WHERE id = %s AND service_id = %s", (item_id, service_id))
        existing_item = db.cursor.fetchone()
        validate_item_request_exists(existing_item, item_id)

        update_data = item.dict(exclude_unset=True)

        # Prevent product_variant_id updates
        if "product_variant_id" in update_data:
            if update_data["product_variant_id"] != existing_item["product_variant_id"]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product variant cannot be changed after creation")
            update_data.pop("product_variant_id")

        # Ensure at least one field is being updated
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid fields provided for update")
        
        sql, values = dynamic_patch_query("item_requests", data=item.dict(exclude_unset=True), table_id=item_id, service_id=service_id)
        db.cursor.execute(sql, values)
        updated_item_request = db.cursor.fetchone()

        db.conn.commit()
        return type_of_service_relationship(updated_item_request, db)

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        db.conn.rollback()
        exception(e)