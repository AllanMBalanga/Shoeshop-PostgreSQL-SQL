from fastapi import status, HTTPException, APIRouter
from ..body import ProductVariant
from ..database import Database
from ..update import ProductVariantPatch, ProductVariantPut, dynamic_patch_query
from ..response import ProductVariantResponse
from typing import List
from ..status_code import validate_product_exists, validate_variant_exists, exception
from ..relationships import variant_relationship

router = APIRouter(
    prefix="/products/{product_id}/variants",
    tags=["Product Variants"]
)

db = Database()


@router.get("/", response_model=List[ProductVariantResponse])
def get_variants(product_id: int):
    db.cursor.execute("SELECT * FROM product_variants WHERE product_id = %s", (product_id,))
    variants = db.cursor.fetchall()
    validate_variant_exists(variants, product_id)

    return [variant_relationship(variant, db) for variant in variants]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProductVariantResponse)
def create_variant(product_id: int, variant: ProductVariant):
    try:
        db.cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = db.cursor.fetchone()
        validate_product_exists(product, product_id)

        variant_data = variant.dict()
        variant_data["product_id"] = product_id

        db.cursor.execute(
            "INSERT INTO product_variants (size, color, stock_quantity, product_id) VALUES (%s, %s, %s, %s) RETURNING *", 
            tuple(variant_data.values())
            )
        created_variant = db.cursor.fetchone()

        db.conn.commit()
        return variant_relationship(created_variant, db)

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        db.conn.rollback()
        exception(e)


@router.get("/{variant_id}", response_model=ProductVariantResponse)
def get_variant_by_id(product_id: int, variant_id: int):
    db.cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = db.cursor.fetchone()
    validate_product_exists(product, product_id)

    db.cursor.execute("SELECT * FROM product_variants WHERE id = %s AND product_id = %s", (variant_id, product_id))
    variant = db.cursor.fetchone()
    validate_variant_exists(variant, variant_id)

    return variant_relationship(variant, db)


@router.delete("/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variant(product_id: int, variant_id: int):
    try:
        db.cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = db.cursor.fetchone()
        validate_product_exists(product, product_id)

        db.cursor.execute("DELETE FROM product_variants WHERE id = %s AND product_id = %s RETURNING", (variant_id, product_id))
        variant = db.cursor.fetchone()
        validate_variant_exists(variant, variant_id)

        db.conn.commit()
        return

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        db.conn.rollback()
        exception(e)


@router.put("/{variant_id}", response_model=ProductVariantResponse)
def put_variant(product_id: int, variant_id: int, variant: ProductVariantPut):
    try:
        db.cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = db.cursor.fetchone()
        validate_product_exists(product, product_id)
        db.cursor.execute(
            "UPDATE product_variants " \
            "SET size = %s, color = %s, stock_quantity = %s " \
            "WHERE id = %s AND product_id = %s RETURNING *", 
            tuple(variant.dict().values()) + (variant_id, product_id))
        
        updated_variant = db.cursor.fetchone()
        validate_variant_exists(updated_variant, variant_id)

        db.conn.commit()
        return variant_relationship(updated_variant, db)

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        db.conn.rollback()
        exception(e)


@router.patch("/{variant_id}", response_model=ProductVariantResponse)
def patch_variant(product_id: int, variant_id: int, variant: ProductVariantPatch):
    try:
        db.cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = db.cursor.fetchone()
        validate_product_exists(product, product_id)

        sql, values = dynamic_patch_query("product_variants", data=variant.dict(exclude_unset=True), table_id=variant_id, product_id=product_id)
        db.cursor.execute(sql, values)
        updated_variant = db.cursor.fetchone()
        validate_variant_exists(updated_variant, variant_id)

        db.conn.commit()
        return variant_relationship(updated_variant, db)

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        db.conn.rollback()
        exception(e)