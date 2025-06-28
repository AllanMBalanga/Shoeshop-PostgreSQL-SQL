# Shoeshop-PostgreSQL-SQL
Shoeshop database: Managing customer sales and repairs (SQL queries)

### Database Structure (6 tables)
- Customers - Client relationship management
- Service Requests - Order processing pipeline
- Products & Product Variants - Inventory catalog system
- Repairs - Service workflow tracking
- Item Requests - Sales order management

### Tech Stack
- Language: Python
- API Framework: FastAPI 
- Database: PostgreSQL
- SQL Access: psycopg2
- Validation: Pydantic
- Security: bcrypt, JWT 
- Testing: Postman 
- Tools: Uvicorn

## Dependencies
Make sure to install the following libraries before running the project:

- fastapi
- psycopg2
- uvicorn
- bcrypt
- pydantic
- jwt

Install them using:

```bash
pip install -r requirements.txt
