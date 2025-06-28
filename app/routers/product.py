from fastapi import status, HTTPException, APIRouter
from typing import List
from ..body import Product
from ..update import ProductPatch, ProductPut, dynamic_patch_query
from ..response import ProductResponse
from ..database import Database
from ..status_code import validate_product_exists, exception
from ..relationships import product_relationship

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

db = Database()


@router.get("/", response_model=List[ProductResponse])
def get_products():
    db.cursor.execute("SELECT * FROM products")
    products = db.cursor.fetchall()

    return [product_relationship(product, db) for product in products]


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_product(product: Product):
    try:
        db.cursor.execute(
            "INSERT INTO products (name, description, price, stock_quantity) VALUES (%s, %s, %s, %s) RETURNING *",
            tuple(product.dict().values())
            )
        product = db.cursor.fetchone()

        db.conn.commit()
        return product

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        db.conn.rollback()
        exception(e)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product_by_id(product_id: int):
    db.cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = db.cursor.fetchone()
    validate_product_exists(product, product_id)

    return product_relationship(product, db)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int):
    try:
        db.cursor.execute("DELETE FROM products WHERE id = %s RETURNING *", (product_id,))    
        product = db.cursor.fetchone()
        validate_product_exists(product, product_id)

        db.conn.commit()
        return

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        db.conn.rollback()
        exception(e)


@router.put("/{product_id}", response_model=ProductResponse)
def put_product(product_id: int, product: ProductPut):
    try:
        db.cursor.execute(
            "UPDATE products SET name = %s, description = %s, price = %s, stock_quantity = %s WHERE id = %s RETURNING *", 
            tuple(product.dict().values()) + (product_id,)
            )
        updated_product = db.cursor.fetchone()
        validate_product_exists(product, product_id)

        db.conn.commit()
        return product_relationship(updated_product, db)

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        db.conn.rollback()
        exception(e)

@router.patch("/{product_id}", response_model=ProductResponse)
def patch_product(product_id: int, product: ProductPatch):
    try:
        sql, values = dynamic_patch_query("products", product.dict(exclude_unset=True), table_id=product_id)
        db.cursor.execute(sql, values)
        updated_customer = db.cursor.fetchone()
        validate_product_exists(product, product_id)
        
        db.conn.commit()
        return product_relationship(updated_customer, db)

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        db.conn.rollback()
        exception(e)
