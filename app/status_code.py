from fastapi import status, HTTPException

def exception(e):
    print(f"Request error {e}")
    raise HTTPException(status_code=500, detail=f"Something went wrong")

#check if repair exists in database
def validate_repair_exists(repair, repair_id: int = None):
    if not repair:
        if repair_id:
            detail = f"Repair with id {repair_id} was not found"
        else:
            detail = "Repair was not found"
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=detail
        )


#check if customer.id is in database
def validate_customer_exists(customer, customer_id: int = None):
    if not customer:
        if customer_id:
            detail = f"Customer with id {customer_id} was not found" 
        else:
            detail = "Customer was not found"

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=detail
        )


#check if service exists in database
def validate_service_exists(service, service_id: int = None):
    if not service:
        if service_id:
            detail = f"Service with id {service_id} was not found"
        else:
            detail = "Service was not found"
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=detail
        )


#check if type of service
def validate_service_type(service, expected_type: str):
    if service["type"] != expected_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected service type: {expected_type}. Type recieved: {service['type']}"
        )


#check if customer.id is the one that created the account before posting/deleting/updating
def validate_customer_ownership(customer_id: int, current_user_id: int):
    if customer_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized to perform this action on this customer"
        )


#check if repair exists in database
def validate_item_request_exists(item_request, item_id: int = None):
    if not item_request:
        if item_id:
            detail = f"Item request with id {item_id} was not found"
        else:
            detail = "Item request was not found"
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=detail
        )
    

#check if product exists in database
def validate_product_exists(product, product_id: int = None):
    if not product:
        if product_id:
            detail = f"Product with id {product_id} was not found" 
        else:
            detail = "Product was not found"

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=detail
        )


#check if variants exists in database
def validate_variant_exists(variant, variant_id: int = None):
    if not variant:
        if variant_id:
            detail = f"Product variant with id {variant_id} was not found" 
        else:
            detail = "Product variant was not found"

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=detail
        )


