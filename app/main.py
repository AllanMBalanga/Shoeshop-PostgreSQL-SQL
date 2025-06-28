from fastapi import FastAPI
from app.routers import customers, service, product, variant, repairs, items, login
from .database import Database

app = FastAPI()

app.include_router(customers.router)
app.include_router(service.router)
app.include_router(product.router)
app.include_router(variant.router)
app.include_router(repairs.router)
app.include_router(items.router)
app.include_router(login.router)

# Initialize the database and create tables on startup if there are any new tables created
@app.on_event("startup")
def startup():
    db = Database()
    db.create_tables()
