from .database import Database

def customer_relationship(customer, db: Database):
    db.cursor.execute("SELECT * FROM service_requests WHERE customer_id = %s", (customer["id"],))
    services = db.cursor.fetchall()

    return {
        **customer,
        "services": services
        }


def service_relationship(service, db: Database):
    db.cursor.execute("SELECT * FROM customers WHERE id = %s", (service["customer_id"],))
    user = db.cursor.fetchone()

    db.cursor.execute("SELECT * FROM repairs WHERE service_id = %s", (service["id"],))
    repair = db.cursor.fetchall()

    db.cursor.execute("SELECT * FROM item_requests WHERE service_id = %s", (service["id"],))
    item_request = db.cursor.fetchall()

    return {
        **service, 
        "user": user,
        "repairs": repair,
        "items": item_request
        }


def product_relationship(product, db: Database):
    db.cursor.execute("SELECT * FROM product_variants WHERE product_id = %s", (product["id"],))
    variants = db.cursor.fetchall()
    product["variants"] = variants

    return {
        **product, 
        "variants": variants
        }


def variant_relationship(variant, db: Database):
    db.cursor.execute("SELECT * FROM products WHERE id = %s", (variant["product_id"],))
    product = db.cursor.fetchone()

    return {
        **variant, 
        "product": product
        }


def type_of_service_relationship(service_type, db: Database):
    db.cursor.execute("SELECT * FROM service_requests WHERE id = %s", (service_type["service_id"],))
    service = db.cursor.fetchone()

    return {
        **service_type, 
        "service": service
        }

