import sqlite3
from utilis import hash_password, verify_password
from models import UserCreate, SellerCreate, CreateProduct, UserLogin, UserRefresh, CreateOrder, UpdateStock
from jwt_handler import create_access_token, create_refresh_token, decode_token
from datetime import date
from database import DATABASE_URL
from logger import logger
from fastapi import File, UploadFile
import shutil
import os

# ============ HELPER FUNCTIONS ===========

def generic_insert(table_name: str, columns: list, values: tuple):
    """
    Generic helper function to insert data into any table
    Args:
        table_name: Name of the table (e.g., 'users', 'sellers', 'products')
        columns: List of column names (e.g., ['name', 'email', 'password'])
        values: Tuple of values to insert
    Returns:
        dict with inserted_id or error
    """
    try:
        with sqlite3.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            
            # Build dynamic SQL query
            placeholders = ','.join(['?' for _ in columns])
            columns_str = ','.join(columns)
            
            query = f'INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})'
            
            cursor.execute(query, values)
            conn.commit()
            
            inserted_id = cursor.lastrowid
            return {"success": True, "id": inserted_id}
    except sqlite3.IntegrityError as e:
        return {"error": f"Integrity error: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}


def get_user_by_email(email: str):
    """Fetch user from database by email"""
    try:
        with sqlite3.connect(DATABASE_URL) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            
            if not user:
                return {"error": "User not found"}
            return {"user": user}
    except Exception as e:
        return {"error": str(e)}

def get_current_user(token: str):
    payload = decode_token(token)
    if "error" in payload:
        return payload
    email = payload["email"]
    user_result = get_user_by_email(email)
    if "error" in user_result:
        return {"error": "Invalid Token"}
    return dict(user_result["user"])


# ============ BUSINESS LOGIC ============

# Business logic functions for user registration
def register_user(User: UserCreate):
    try:
        hashed_password = hash_password(User.password)
        
        result = generic_insert(
            table_name='users',
            columns=['name', 'email', 'password', 'role'],
            values=(User.name, User.email, hashed_password, User.role)
        )
        
        if "error" in result:
            logger.error(f"register user failed: {result['error']}")
            return result
        
        return {"message": "User registered successfully", "user_id": result["id"]}
    except Exception as e:
        logger.error(f"register_user exception: {str(e)}")
        return {"error": str(e)}
    
def register_seller(seller: SellerCreate):
    try:
        hashed_password = hash_password(seller.password)
        
        # Step 1: Insert user
        user_result = generic_insert(
            table_name='users',
            columns=['name', 'email', 'password', 'role'],
            values=(seller.name, seller.email, hashed_password, seller.role)
        )
        
        if "error" in user_result:
            return user_result
        
        user_id = user_result["id"]
        
        # Step 2: Insert seller details
        seller_result = generic_insert(
            table_name='sellers',
            columns=['user_id', 'business_name', 'gst_number', 'phone', 'address'],
            values=(user_id, seller.business_name, seller.gst_number, seller.phone, seller.address)
        )
        
        if "error" in seller_result:
            return seller_result
        
        return {
            "message": "Seller registered successfully",
            "user_id": user_id,
            "note": "Wait for admin verification before adding products"
        }
    except sqlite3.IntegrityError as e:
        if "email" in str(e).lower():
            return {"error": "Email already exists"}
        elif "gst_number" in str(e).lower():
            return {"error": "GST number already exists"}
        else:
            return {"error": "Registration failed - duplicate entry"}
    except Exception as e:
        return {"error": str(e)}
            

def authenticate_user(User: UserLogin):
    """Handle user authentication logic"""
    try:
        # Use helper function to fetch user
        user_result = get_user_by_email(User.email)
        
        if "error" in user_result:
            return user_result
        
        user = user_result["user"]
        
        # Verify password
        is_valid = verify_password(User.password, user["password"])
        if not is_valid:
            return {"error": "Invalid password"}
        
        # Create tokens
        access_token = create_access_token({
            "email": user["email"],
            "name": user["name"],
            "role": user["role"]
        })
        
        refresh_token = create_refresh_token({
            "email": user["email"],
            "name": user["name"],
            "role": user["role"]
        })
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        return {"error": str(e)} 
        
def refresh(token: UserRefresh):
    payload = decode_token(token.token)
    token_type = payload["token_type"]
    email = payload["email"]

    if token_type != "refresh":
        return {"error": "Invalid token"}
    
    user_result = get_user_by_email(email)

    if "error" in user_result:
        return user_result
    
    user = user_result["user"]

    access_token = create_access_token({
            "email": user["email"],
            "name": user["name"],
            "role": user["role"]
        })
        
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# Business logic for product operations
def create_product(Product: CreateProduct, token: str):
    user = get_current_user(token)
    if "error" in user:
        return user
    if user["role"] != "seller":
        return {"error": "Unauthorized"}
    
    try:
        Product_result = generic_insert(
            table_name='products',
            columns=['name', 'description', 'price', 'category', 'stock_quantity','tax','expiry_date'],
            values=(Product.name, Product.description, Product.price, Product.category, Product.stock_quantity, Product.tax,Product.expiry_date))

        if "error" in Product_result:
            return Product_result
        return {"message": "Product Created successfully"}
    except Exception as e:
        return {"error": str(e)}
    


def get_product(product_id: int):
    with sqlite3.connect(DATABASE_URL) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()

        if not product:
            return {"error": "Product Not Found"}
        return dict(product)
    
def get_products():
    with sqlite3.connect(DATABASE_URL) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()

        if not products:
            return {"error": "Products Not Found"}
        return [dict(product) for product in products]


def place_customer_order(Order: CreateOrder, token: str):
    user = get_current_user(token)
    if "error" in user:
        return user
    customer_id = user["id"]
    
    product = get_product(Order.product_id)
    if "error" in product:
        return product
    
    if product["expiry_date"]:
        if date.fromisoformat(product["expiry_date"]) < date.today():
            with sqlite3.connect(DATABASE_URL) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM products WHERE id = ?", (Order.product_id,))
                conn.commit()
                return {"error": "Product not available"}
        
    if product["stock_quantity"] < Order.quantity:
        return {"error": "Insufficient stock"}

    try:
        order_result = generic_insert(
            table_name='customer_orders',
            columns=['customer_id', 'product_id', 'quantity', 'status'],
            values=(customer_id, Order.product_id, Order.quantity, 'pending'))

        
        if "error" in order_result:
            return order_result
        
        with sqlite3.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ?",
                          (Order.quantity, Order.product_id))
            conn.commit()

        return {"message": "Product Placed successfully!, We will notify you when it will be placed"}
    except Exception as e:
        return {"error": str(e)}

def check_low_stock(token: str):
    user = get_current_user(token)
    if "error" in user:
        return user
    if not user:
        return {"error": "User not found"}
    if user["role"] != "seller":
        return {"error": "Unauthorized"}
    
    with sqlite3.connect(DATABASE_URL) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE stock_quantity < 10")
        products = cursor.fetchall()

        if not products:
            return {"message": "All products have sufficient stock"}
        
        return [dict(product) for product in products]

def update_stock(Stock: UpdateStock, token: str):
    user = get_current_user(token)
    if "error" in user:
        return user
    if not user:
        return {"error": "User not found"}
    if user["role"] != "seller":
        return {"error": "Unauthorized"}
  
    
    with sqlite3.connect(DATABASE_URL) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?",
                    (Stock.stock_quantity, Stock.product_id))
        
        conn.commit()
        return {"message": "Stock updated successfully"}
    
def get_orders(token:str):
    user = get_current_user(token)
    if "error" in user:
        return user
    if not user:
        return {"error": "User not found"}
    if user["role"] != "seller":
        return {"error": "Unauthorized"}
    
    with sqlite3.connect(DATABASE_URL) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customer_orders")
        orders = cursor.fetchall()

        if not orders:
            return {"error": "No orders to show"}
        
        return [dict(order) for order in orders]
    
def check_expiry(token: str):
    user = get_current_user(token)
    if "error" in user:
        return user
    if not user:
        return {"error": "User not found"}
    if user["role"] != "seller":
        return {"error": "Unauthorized"}
    
    with sqlite3.connect(DATABASE_URL) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()

        result = []
        today = date.today()

        for product in products:
            p = dict(product)

            if not p["expiry_date"]:
                continue

            expiry = date.fromisoformat (p["expiry_date"])
            days_left = (expiry - today).days

            if days_left < 0:
                p["expiry_status"] = "expired"
            elif days_left <= 60:
                p["expiry_status"] = f"warning - {days_left} days left"
            else:
                p["expiry_status"]= "safe"

            result.append(p)

        return result   

async def upload_product_image(product_id: int, file: UploadFile, token:str):
    user = get_current_user(token)
    if "error" in user:
        return user
    if user["role"] != "seller":
        return {"error": "Unauthorized"}

    allowed = ["image/jpeg", "image/png"]
    if file.content_type not in allowed:
        return {"error": "Only JPG/PNG allowed"}
    
    file_path = f"uploads/{product_id}_{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"message": "Image uploaded!", "path": file_path}

async def upload_seller_document(seller_id: int, file: UploadFile, token: str):
    user = get_current_user(token)
    if "error" in user:
        return user
    if user['role'] != "seller":
        return {"error": "Unauthorized"}

    allowed = ["application/pdf"]
    if file.content_type not in allowed:
        return {"error": "Sirf PDF allowed hai"}

    file_path = f"uploads/{seller_id}_{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"message": "Document uploaded!", "path": file_path}