from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

def create_access_token(data):
    payload = data.copy()

    expiry = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload.update({
        "iat": datetime.utcnow(),
        "exp": expiry,
        "token_type": "access"
    })

    to_encode = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return to_encode

def create_refresh_token(data):
    payload = data.copy()

    expiry = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    payload.update({
        "iat": datetime.utcnow(),
        "exp": expiry,
        "token_type": "refresh"
    })

    to_encode = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return to_encode

def decode_token(token: str):
    try:
        to_decode = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return to_decode
    except ExpiredSignatureError:
        return {"error": "Token expired"}
    except JWTError:
        return {"error": "Invalid token"}
    except Exception as e:
        return {"error": str(e)}