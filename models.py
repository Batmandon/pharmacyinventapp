from pydantic import BaseModel
from datetime import date

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str  # "user" or "seller"

class SellerCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "seller"
    business_name: str
    gst_number: str
    phone: str
    address: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserRefresh(BaseModel):
    token: str

class CreateProduct(BaseModel):
    name: str
    description: str | None = None
    price: float
    category: str | None = None
    stock_quantity: int
    tax: float | None = None
    expiry_date: date

class CreateOrder(BaseModel):
    product_id: int
    quantity: int

class UpdateStock(BaseModel):
    product_id: int
    stock_quantity: int