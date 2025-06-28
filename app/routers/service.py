from fastapi import status, HTTPException, APIRouter, Depends
from ..response import ServiceResponse
from ..update import ServiceRequestPatch, ServiceRequestPut, dynamic_patch_query
from ..database import Database
from ..body import ServiceRequest, TokenData
from typing import List
from ..status_code import validate_customer_exists, validate_service_exists, exception, validate_customer_ownership
from ..oauth2 import get_current_user
from ..relationships import service_relationship

router = APIRouter(
    prefix="/customers/{customer_id}/services",
    tags=["Service Requests"]
)

db = Database()


@router.get("/", response_model=List[ServiceResponse])
def get_services(customer_id: int):
    db.cursor.execute("SELECT * FROM service_requests WHERE customer_id = %s", (customer_id,))
    services = db.cursor.fetchall()
    validate_customer_exists(services, customer_id)

    return [service_relationship(service, db) for service in services]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ServiceResponse)
def create_service(customer_id: int, service: ServiceRequest, current_user: TokenData = Depends(get_current_user)):
    try:
        db.cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = db.cursor.fetchone()
        validate_customer_exists(customer, customer_id)
        validate_customer_ownership(customer["id"], current_user.id)

        service_data = service.dict()
        service_data["customer_id"] = customer_id

        db.cursor.execute(
            "INSERT INTO service_requests (total_cost, type, customer_id) VALUES (%s, %s, %s) RETURNING *", 
            tuple(service_data.values())
            )
        created_service = db.cursor.fetchone()
        db.conn.commit()
        return service_relationship(created_service, db)
    
    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        db.conn.rollback()
        exception(e)


@router.get("/{service_id}", response_model=ServiceResponse)
def get_service_by_id(customer_id: int, service_id: int):
    db.cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
    customer = db.cursor.fetchone()
    validate_customer_exists(customer, customer_id)

    db.cursor.execute("SELECT * FROM service_requests WHERE id = %s AND customer_id = %s", (service_id, customer_id))
    service = db.cursor.fetchone()
    validate_service_exists(service, service_id)

    return service_relationship(service, db)


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(customer_id: int, service_id: int, current_user: TokenData = Depends(get_current_user)):
    try:
        db.cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = db.cursor.fetchone()
        validate_customer_exists(customer, customer_id)

        db.cursor.execute("DELETE FROM service_requests WHERE id = %s AND customer_id = %s RETURNING *", (service_id, customer_id))
        service = db.cursor.fetchone()
        validate_service_exists(service, service_id)
        validate_customer_ownership(service["customer_id"], current_user.id)

        db.conn.commit()
        return
    
    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        db.conn.rollback()
        exception(e)


@router.put("/{service_id}", response_model=ServiceResponse)
def put_service(customer_id: int, service_id: int, service: ServiceRequestPut, current_user: TokenData = Depends(get_current_user)):
    try:
        db.cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = db.cursor.fetchone()
        validate_customer_exists(customer, customer_id)

        db.cursor.execute(
            "UPDATE service_requests " \
            "SET total_cost = %s, type = %s " \
            "WHERE id = %s AND customer_id = %s RETURNING *", 
            tuple(service.dict().values()) + (service_id, customer_id))
        updated_service = db.cursor.fetchone()
        validate_service_exists(updated_service, service_id)
        validate_customer_ownership(updated_service["customer_id"], current_user.id)

        db.conn.commit()
        return service_relationship(updated_service, db)
    
    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        db.conn.rollback()
        exception(e)


@router.patch("/{service_id}", response_model=ServiceResponse)
def patch_service(customer_id: int, service_id: int, service: ServiceRequestPatch, current_user: TokenData = Depends(get_current_user)):
    try:
        db.cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = db.cursor.fetchone()
        validate_customer_exists(customer, customer_id)

        sql, values = dynamic_patch_query("service_requests", data=service.dict(exclude_unset=True), table_id=service_id, customer_id=customer_id)
        db.cursor.execute(sql, values)
        updated_service = db.cursor.fetchone()
        validate_service_exists(updated_service, service_id)
        validate_customer_ownership(updated_service["customer_id"], current_user.id)
        
        db.conn.commit()
        return service_relationship(updated_service, db)
    
    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        db.conn.rollback()
        exception(e)
    