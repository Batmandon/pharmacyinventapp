from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from database import create_database, DATABASE_URL
from models import UserCreate, UserLogin, UserRefresh, SellerCreate, CreateProduct, CreateOrder, UpdateStock
from Businesslogic import register_user,authenticate_user, create_product, refresh, get_product, register_seller, get_products,place_customer_order, check_low_stock, update_stock, get_orders, check_expiry

app = FastAPI()
create_database(DATABASE_URL)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

@app.post("/register")
def register(User: UserCreate):
    """Endpoint to register a new user"""
    result = register_user(User)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/register/seller")
def register(User: SellerCreate):
    """Endpoint to register a new user"""
    result = register_seller(User)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/login")
def login(login: UserLogin):
    result = authenticate_user(login)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.post("/refresh") 
def refresh_token(token: UserRefresh):
    result = refresh(token)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.post("/create/products")
def add_product(product: CreateProduct, token: str = Depends(oauth2_scheme)):
    result = create_product(product, token)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/product/{product_id}")
def see_product(product_id: int):
    result = get_product(product_id)
    if "error" in result:
        raise HTTPException(status_code=404,  detail=result["error"])
    return result

@app.get("/products/lowstock")
def low_stock(token: str = Depends(oauth2_scheme)):
    result = check_low_stock(token)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
   
@app.get("/products")
def see_products():
    result = get_products()
    if "error" in result:
        raise HTTPException(status_code=404,  detail=result["error"])
    return result

@app.post("/place/order")
def place_order(order: CreateOrder,token: str = Depends(oauth2_scheme)):
    result = place_customer_order(order, token)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/update/stock")
def stock_update(stock: UpdateStock, token: str = Depends(oauth2_scheme)):
    result = update_stock(stock, token)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/orders")
def see_orders(token: str = Depends(oauth2_scheme)):
    result = get_orders(token)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/check/expiry")
def expiry_check(token: str = Depends(oauth2_scheme)):
    result = check_expiry(token)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

