import psycopg2
from psycopg2.extras import RealDictCursor
from .config import settings

class Database:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                host=settings.database_hostname,
                database=settings.database_name,
                user=settings.database_server,
                password=settings.database_password,
                cursor_factory=RealDictCursor)
            
            self.cursor = self.conn.cursor()

        except Exception as e:
            print(f"Connetion to database failed. Error: {e}")

    #altered password to handle total number of text after password hashing
    def create_tables(self):
        commands = (
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'request_type') THEN
                    CREATE TYPE request_type AS ENUM ('sale', 'repair');
                END IF;

                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_type') THEN CREATE TYPE
                    status_type AS ENUM ('pending', 'in_progress', 'completed');
                END IF;
            END$$;
            """,
            """
            CREATE TABLE IF NOT EXISTS customers(
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL, 
                email VARCHAR(64) NOT NULL UNIQUE, 
                password VARCHAR(32) NOT NULL,          
                address VARCHAR(255) NOT NULL, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """,
            """
                CREATE TABLE IF NOT EXISTS service_requests(
                id SERIAL PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                total_cost FLOAT DEFAULT 0,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                type request_type,

                -- foreign keys --
                FOREIGN KEY (customer_id) REFERENCES customers (id)
                ON UPDATE CASCADE ON DELETE CASCADE
                );
            """,
            """
                CREATE TABLE IF NOT EXISTS products(
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description VARCHAR(255) NOT NULL,
                price FLOAT NOT NULL,
                stock_quantity INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                -- constraints
                CONSTRAINT check_positive_price CHECK (price >= 0),
                CONSTRAINT check_stock_positive CHECK (stock_quantity >= 0)
                );
            """,
            """
                CREATE TABLE IF NOT EXISTS product_variants(
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL,
                size VARCHAR(32) NOT NULL,
                color VARCHAR(32) NOT NULL,
                stock_quantity INTEGER NOT NULL DEFAULT 0,
                
                -- foreign key
                FOREIGN KEY (product_id) REFERENCES products (id)
                ON UPDATE CASCADE ON DELETE CASCADE,

                -- constraints
                CONSTRAINT check_variant_stock_positive CHECK (stock_quantity >= 0)
                );
            """,
            """
                CREATE TABLE IF NOT EXISTS repairs(
                id SERIAL PRIMARY KEY,
                service_id INTEGER NOT NULL,
                description VARCHAR(255) NOT NULL,
                status status_type,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                start_date TIMESTAMP DEFAULT NULL,
                finished_date TIMESTAMP DEFAULT NULL,
                FOREIGN KEY (service_id) REFERENCES service_requests (id)
                ON UPDATE CASCADE ON DELETE CASCADE
                );
            """,
            """
                CREATE TABLE IF NOT EXISTS item_requests (
                id SERIAL PRIMARY KEY,
                service_id INTEGER NOT NULL,
                product_variant_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price FLOAT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- foreign
                FOREIGN KEY (service_id) REFERENCES service_requests (id)
                ON UPDATE CASCADE ON DELETE CASCADE,
                FOREIGN KEY (product_variant_id) REFERENCES product_variants (id)
                ON UPDATE CASCADE ON DELETE CASCADE,

                -- constraints
                CONSTRAINT unique_request_variant UNIQUE (service_id, product_variant_id),
                CONSTRAINT check_positive_quantity CHECK (quantity > 0),
                CONSTRAINT check_positive_price CHECK (unit_price >= 0)
                );
            """
        )
        for command in commands:
            self.cursor.execute(command)
        self.conn.commit()
        self.conn.close()