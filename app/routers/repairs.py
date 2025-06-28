from fastapi import status, HTTPException, APIRouter, Depends
from datetime import datetime
from ..body import Repair, TokenData
from ..response import RepairResponse
from ..update import RepairPatch, RepairPut, dynamic_patch_query
from ..database import Database
from typing import List
from ..status_code import validate_service_type, validate_customer_exists, validate_customer_ownership, validate_service_exists, validate_repair_exists, exception
from ..oauth2 import get_current_user
from ..relationships import type_of_service_relationship

router = APIRouter(
    prefix="/customers/{customer_id}/services/{service_id}/repairs",
    tags=["Repairs"]
)

db = Database()


@router.get("/", response_model=List[RepairResponse])
def get_repairs(customer_id: int, service_id: int):
    db.cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
    customer = db.cursor.fetchone()
    validate_customer_exists(customer, customer_id)

    db.cursor.execute("SELECT * FROM service_requests WHERE id = %s AND customer_id = %s", (service_id, customer_id))
    service = db.cursor.fetchone()
    validate_service_exists(service, service_id)
    validate_service_type(service, "repair")

    db.cursor.execute("SELECT * FROM repairs WHERE service_id = %s", (service_id,))
    repairs = db.cursor.fetchall()

    return [type_of_service_relationship(repair, db) for repair in repairs]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=RepairResponse)
def create_repair(customer_id: int, service_id: int, repair: Repair, current_user: TokenData = Depends(get_current_user)):
    try:
        db.cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = db.cursor.fetchone()
        validate_customer_exists(customer, customer_id)

        db.cursor.execute("SELECT * FROM service_requests WHERE id = %s AND customer_id = %s", (service_id, customer_id))
        service = db.cursor.fetchone()
        validate_service_exists(service, service_id)
        validate_service_type(service, "repair")
        validate_customer_ownership(service["customer_id"], current_user.id)

        repair_data = repair.dict()
        repair_data["service_id"] = service_id

        db.cursor.execute(
            "INSERT INTO repairs (description, status, service_id) VALUES (%s, %s, %s) RETURNING *", 
            tuple(repair_data.values())
            )
        created_repair = db.cursor.fetchone()

        if created_repair["status"] == "in_progress":
            start_date = datetime.utcnow()
            db.cursor.execute(
                "UPDATE repairs SET start_date = %s WHERE id = %s",
                (start_date, created_repair["id"])
            )
            created_repair["start_date"] = start_date

        elif created_repair["status"] == "completed":
            finished_date = datetime.utcnow()
            db.cursor.execute(
                "UPDATE repairs SET finished_date = %s WHERE id = %s",
                (finished_date, created_repair["id"])
            )
            created_repair["finished_date"] = finished_date

        db.conn.commit()
        return type_of_service_relationship(created_repair, db)

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        db.conn.rollback()
        exception(e)
    

@router.get("/{repair_id}", response_model=RepairResponse)
def get_repair_by_id(customer_id: int, service_id: int, repair_id: int):
    db.cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
    customer = db.cursor.fetchone()
    validate_customer_exists(customer, customer_id)

    db.cursor.execute("SELECT * FROM service_requests WHERE id = %s AND customer_id = %s", (service_id, customer_id))
    service = db.cursor.fetchone()
    validate_service_exists(service, service_id)

    validate_service_type(service, "repair")

    db.cursor.execute("SELECT * FROM repairs WHERE id = %s AND service_id = %s", (repair_id, service_id))
    repair = db.cursor.fetchone()
    validate_repair_exists(repair, repair_id)

    return type_of_service_relationship(repair, db)


@router.delete("/{repair_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repair(customer_id: int, service_id: int, repair_id: int, current_user: TokenData = Depends(get_current_user)):
    try:
        db.cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = db.cursor.fetchone()
        validate_customer_exists(customer, customer_id)

        db.cursor.execute("SELECT * FROM service_requests WHERE id = %s AND customer_id = %s", (service_id, customer_id))
        service = db.cursor.fetchone()
        validate_service_exists(service, service_id)
        validate_service_type(service, "repair")
        validate_customer_ownership(service["customer_id"], current_user.id)

        db.cursor.execute("DELETE FROM repairs WHERE id = %s AND service_id = %s RETURNING *", (repair_id, service_id))
        repair = db.cursor.fetchone()
        validate_repair_exists(repair, repair_id)
        
        db.conn.commit()
        return

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        db.conn.rollback()
        exception(e)
    

@router.put("/{repair_id}", response_model=RepairResponse)
def put_repair(customer_id: int, service_id: int, repair_id: int, repair: RepairPut, current_user: TokenData = Depends(get_current_user)):
    try:
        # Validate customer
        db.cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = db.cursor.fetchone()
        validate_customer_exists(customer, customer_id)

        # Validate service request
        db.cursor.execute("SELECT * FROM service_requests WHERE id = %s AND customer_id = %s", (service_id, customer_id))
        service = db.cursor.fetchone()
        validate_service_exists(service, service_id)
        validate_service_type(service, "repair")
        validate_customer_ownership(service["customer_id"], current_user.id)

        # Get existing repair to compare previous status
        db.cursor.execute("SELECT * FROM repairs WHERE id = %s AND service_id = %s", (repair_id, service_id))
        existing_repair = db.cursor.fetchone()
        validate_repair_exists(existing_repair, repair_id)

        previous_status = existing_repair["status"]
        new_status = repair.status

        # Perform the update
        db.cursor.execute(
            "UPDATE repairs SET description = %s, status = %s WHERE id = %s AND service_id = %s RETURNING *",
            tuple(repair.dict().values()) + (repair_id, service_id)
        )
        updated_repair = db.cursor.fetchone()

        def update_timestamp(column: str, value, repair_id: int):
            db.cursor.execute(
                f"UPDATE repairs SET {column} = %s WHERE id = %s",
                (value, repair_id)
            )
            updated_repair[column] = value

        # Handle transition logic
        if previous_status == "pending" and new_status == "in_progress":
            update_timestamp("start_date", datetime.utcnow(), repair_id)
        elif previous_status != "pending" and new_status == "pending":
            update_timestamp("start_date", None, repair_id)

        if previous_status != "completed" and new_status == "completed":
            update_timestamp("finished_date", datetime.utcnow(), repair_id)
        elif previous_status == "completed" and new_status != "completed":
            update_timestamp("finished_date", None, repair_id)

        db.conn.commit()
        return type_of_service_relationship(updated_repair, db)

    except HTTPException as http_error:
        raise http_error
 
    except Exception as e:
        db.conn.rollback()
        exception(e)


@router.patch("/{repair_id}", response_model=RepairResponse)
def patch_repair(customer_id: int, service_id: int, repair_id: int, repair: RepairPatch, current_user: TokenData = Depends(get_current_user)):
    try:
        db.cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = db.cursor.fetchone()
        validate_customer_exists(customer, customer_id)

        db.cursor.execute("SELECT * FROM service_requests WHERE id = %s AND customer_id = %s", (service_id, customer_id))
        service = db.cursor.fetchone()
        validate_service_exists(service, service_id)
        validate_service_type(service, "repair")
        validate_customer_ownership(service["customer_id"], current_user.id)

        # Get existing repair to compare previous status
        db.cursor.execute("SELECT * FROM repairs WHERE id = %s AND service_id = %s", (repair_id, service_id))
        existing_repair = db.cursor.fetchone()
        validate_repair_exists(existing_repair, repair_id)

        previous_status = existing_repair["status"]
        new_status = repair.status
        
        sql, values = dynamic_patch_query("repairs", data=repair.dict(exclude_unset=True), table_id=repair_id, service_id=service_id)
        db.cursor.execute(sql, values)
        updated_repair = db.cursor.fetchone()

        def update_timestamp(column: str, value, repair_id: int):
            db.cursor.execute(
                f"UPDATE repairs SET {column} = %s WHERE id = %s",
                (value, repair_id)
            )
            updated_repair[column] = value

        # Handle transition logic
        if previous_status == "pending" and new_status == "in_progress":
            update_timestamp("start_date", datetime.utcnow(), repair_id)
        elif previous_status != "pending" and new_status == "pending":
            update_timestamp("start_date", None, repair_id)

        if previous_status != "completed" and new_status == "completed":
            update_timestamp("finished_date", datetime.utcnow(), repair_id)
        elif previous_status == "completed" and new_status != "completed":
            update_timestamp("finished_date", None, repair_id)

        db.conn.commit()
        return type_of_service_relationship(updated_repair, db)
    
    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        db.conn.rollback()
        exception(e)