from fastapi import APIRouter, HTTPException, status, Depends
from app.database import get_db, verify_password, hash_password
from app.schemas import UserLogin, UserCreate, UserResponse, TokenResponse
from app.auth import create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email is already registered")
        
        cursor.execute("""
        INSERT INTO users (email, full_name, hashed_password, role, is_active)
        VALUES (?, ?, ?, ?, 1)
        """, (user.email, user.full_name, hash_password(user.password), user.role or 'sales_rep'))
        user_id = cursor.lastrowid
        
        cursor.execute("SELECT id, email, full_name, role, is_active, created_at FROM users WHERE id = ?", (user_id,))
        new_user = dict(cursor.fetchone())
        
        # Log action
        cursor.execute("INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                       (user_id, "USER_REGISTERED", "user", user_id, f"Registered new user {user.email}"))
        
        return new_user

@router.post("/login", response_model=TokenResponse)
def login_user(credentials: UserLogin):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, full_name, hashed_password, role, is_active, created_at FROM users WHERE email = ?", (credentials.email,))
        user = cursor.fetchone()
        if not user or not verify_password(credentials.password, user["hashed_password"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        
        if not user["is_active"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
        
        token = create_access_token(user_id=user["id"], role=user["role"], email=user["email"])
        user_data = UserResponse(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
            is_active=user["is_active"],
            created_at=user["created_at"]
        )
        
        cursor.execute("INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                       (user["id"], "USER_LOGIN", "user", user["id"], "User logged in successfully"))
        
        return TokenResponse(access_token=token, token_type="bearer", user=user_data)

@router.get("/me", response_model=UserResponse)
def get_profile(current_user: dict = Depends(get_current_user)):
    return current_user
