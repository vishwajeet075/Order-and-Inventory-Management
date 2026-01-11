"""
Database initialization script
Run this to populate initial data (products and inventory)
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import Base, ProductDB, InventoryDB

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://orderuser:orderpass@localhost:5432/orderdb"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    """Initialize database with tables and sample data"""

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")

    db = SessionLocal()

    try:
        # Check if data already exists
        existing_products = db.query(ProductDB).count()
        if existing_products > 0:
            print("✓ Database already contains data, skipping initialization")
            return

        # Sample products
        products = [
            ProductDB(id=1, name="Laptop", price=999.99, description="High-performance laptop"),
            ProductDB(id=2, name="Mouse", price=29.99, description="Wireless ergonomic mouse"),
            ProductDB(id=3, name="Keyboard", price=79.99, description="Mechanical keyboard"),
            ProductDB(id=4, name="Monitor", price=299.99, description="27-inch 4K monitor"),
            ProductDB(id=5, name="Headphones", price=149.99, description="Noise-cancelling headphones"),
        ]

        # Sample inventory
        inventory = [
            InventoryDB(id=1, product_id=1, product_name="Laptop", quantity=45, price=999.99),
            InventoryDB(id=2, product_id=2, product_name="Mouse", quantity=150, price=29.99),
            InventoryDB(id=3, product_id=3, product_name="Keyboard", quantity=8, price=79.99),
            InventoryDB(id=4, product_id=4, product_name="Monitor", quantity=30, price=299.99),
            InventoryDB(id=5, product_id=5, product_name="Headphones", quantity=67, price=149.99),
        ]

        # Add to database
        db.add_all(products)
        db.add_all(inventory)
        db.commit()

        print("✓ Sample products added:", len(products))
        print("✓ Sample inventory added:", len(inventory))
        print("\n✅ Database initialization completed successfully!")

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting database initialization...")
    init_database()