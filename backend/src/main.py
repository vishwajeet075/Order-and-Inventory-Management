from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from enum import Enum
import uuid
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://orderuser:orderpass@localhost:5432/orderdb"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy Models
class ProductDB(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String, nullable=True)

class InventoryDB(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False, unique=True)
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    price = Column(Float, nullable=False)

class OrderStatusEnum(str, Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"

class OrderDB(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=False)
    product_id = Column(Integer, nullable=False)
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(SQLEnum(OrderStatusEnum), default=OrderStatusEnum.PENDING)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# Pydantic Models
class Product(BaseModel):
    id: int
    name: str
    price: float
    description: Optional[str] = None

    class Config:
        from_attributes = True

class InventoryItem(BaseModel):
    id: int
    productId: int
    productName: str
    quantity: int
    price: float

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    customerName: str
    customerEmail: EmailStr
    productId: int
    quantity: int

class Order(BaseModel):
    id: str
    customerName: str
    customerEmail: str
    productId: int
    productName: str
    quantity: int
    status: OrderStatusEnum
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# FastAPI App
app = FastAPI(
    title="Order & Inventory Management API",
    description="Production-grade order and inventory management system with PostgreSQL",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Startup event to create tables
@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Order & Inventory Management API",
        "version": "2.0.0",
        "database": "PostgreSQL",
        "status": "running"
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # Test database connection
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("products", response_model=List[Product])
async def get_products(db: Session = Depends(get_db)):
    """Get all available products"""
    products = db.query(ProductDB).all()
    return products

@app.get("products/{product_id}", response_model=Product)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a specific product by ID"""
    product = db.query(ProductDB).filter(ProductDB.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    return product

@app.get("inventory", response_model=List[InventoryItem])
async def get_inventory(db: Session = Depends(get_db)):
    """Get current inventory status"""
    inventory = db.query(InventoryDB).all()
    return [
        InventoryItem(
            id=item.id,
            productId=item.product_id,
            productName=item.product_name,
            quantity=item.quantity,
            price=item.price
        )
        for item in inventory
    ]

@app.get("inventory/{product_id}", response_model=InventoryItem)
async def get_inventory_item(product_id: int, db: Session = Depends(get_db)):
    """Get inventory for a specific product"""
    inventory = db.query(InventoryDB).filter(InventoryDB.product_id == product_id).first()
    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory for product {product_id} not found"
        )
    return InventoryItem(
        id=inventory.id,
        productId=inventory.product_id,
        productName=inventory.product_name,
        quantity=inventory.quantity,
        price=inventory.price
    )

@app.post("orders", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """Create a new order"""

    # Validate product exists
    product = db.query(ProductDB).filter(ProductDB.id == order.productId).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {order.productId} not found"
        )

    # Check inventory availability
    inventory = db.query(InventoryDB).filter(InventoryDB.product_id == order.productId).first()
    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory not found for product {order.productId}"
        )

    if inventory.quantity < order.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient inventory. Available: {inventory.quantity}, Requested: {order.quantity}"
        )

    # Create order
    order_id = f"ORD-{str(uuid.uuid4())[:8].upper()}"
    now = datetime.now()

    new_order = OrderDB(
        id=order_id,
        customer_name=order.customerName,
        customer_email=order.customerEmail,
        product_id=order.productId,
        product_name=product.name,
        quantity=order.quantity,
        status=OrderStatusEnum.PENDING,
        created_at=now,
        updated_at=now
    )

    db.add(new_order)

    # Update inventory
    inventory.quantity -= order.quantity

    db.commit()
    db.refresh(new_order)

    return Order(
        id=new_order.id,
        customerName=new_order.customer_name,
        customerEmail=new_order.customer_email,
        productId=new_order.product_id,
        productName=new_order.product_name,
        quantity=new_order.quantity,
        status=new_order.status,
        createdAt=new_order.created_at,
        updatedAt=new_order.updated_at
    )

@app.get("orders/{order_id}", response_model=Order)
async def get_order(order_id: str, db: Session = Depends(get_db)):
    """Get order details by order ID"""
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )

    return Order(
        id=order.id,
        customerName=order.customer_name,
        customerEmail=order.customer_email,
        productId=order.product_id,
        productName=order.product_name,
        quantity=order.quantity,
        status=order.status,
        createdAt=order.created_at,
        updatedAt=order.updated_at
    )

@app.get("orders", response_model=List[Order])
async def get_all_orders(db: Session = Depends(get_db)):
    """Get all orders"""
    orders = db.query(OrderDB).all()
    return [
        Order(
            id=order.id,
            customerName=order.customer_name,
            customerEmail=order.customer_email,
            productId=order.product_id,
            productName=order.product_name,
            quantity=order.quantity,
            status=order.status,
            createdAt=order.created_at,
            updatedAt=order.updated_at
        )
        for order in orders
    ]

@app.put("orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    new_status: OrderStatusEnum,
    db: Session = Depends(get_db)
):
    """Update order status"""
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )

    order.status = new_status
    order.updated_at = datetime.now()

    db.commit()
    db.refresh(order)

    return {
        "message": f"Order {order_id} status updated to {new_status}",
        "order": Order(
            id=order.id,
            customerName=order.customer_name,
            customerEmail=order.customer_email,
            productId=order.product_id,
            productName=order.product_name,
            quantity=order.quantity,
            status=order.status,
            createdAt=order.created_at,
            updatedAt=order.updated_at
        )
    }

@app.delete("orders/{order_id}")
async def cancel_order(order_id: str, db: Session = Depends(get_db)):
    """Cancel an order and restore inventory"""
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )

    # Restore inventory
    inventory = db.query(InventoryDB).filter(InventoryDB.product_id == order.product_id).first()
    if inventory:
        inventory.quantity += order.quantity

    # Delete order
    db.delete(order)
    db.commit()

    return {"message": f"Order {order_id} cancelled successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)