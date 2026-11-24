from datetime import datetime, timezone
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RefreshToken, User
from app.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    get_refresh_expiry,
    hash_password,
    hash_refresh_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

bearer_scheme = HTTPBearer(auto_error=False)


def issue_tokens(db: Session, user: User) -> dict:
    raw_refresh_token = create_refresh_token()

    token_record = RefreshToken(
        token_hash=hash_refresh_token(raw_refresh_token),
        user_id=user.id,
        expires_at=get_refresh_expiry(),
    )

    db.add(token_record)
    db.commit()

    return {
        "access_token": create_access_token(user.id, user.role),
        "refresh_token": raw_refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "exp", "iat", "type"]},
        )

        if payload.get("type") != "access":
            raise unauthorized

        user_id = int(payload["sub"])

    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        raise unauthorized

    user = db.query(User).filter(User.id == user_id).first()

    if user is None or not user.is_active:
        raise unauthorized

    return user


def require_roles(*roles: str):
    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return current_user

    return role_checker


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    email = str(data.email).strip().lower()

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        full_name=data.full_name.strip(),
        email=email,
        password_hash=hash_password(data.password),
        role="customer",
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to register with these details",
        )

    return user


@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    email = str(data.email).strip().lower()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if (
        user is None
        or not user.is_active
        or not verify_password(data.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    return issue_tokens(db, user)


@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(
    data: RefreshRequest,
    db: Session = Depends(get_db),
):
    token_hash = hash_refresh_token(data.refresh_token)

    stored_token = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .with_for_update()
        .first()
    )

    if stored_token is None or stored_token.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    expiry = stored_token.expires_at

    # SQLite may return a timezone-naive datetime.
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if expiry <= datetime.now(timezone.utc):
        stored_token.revoked = True
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    user = db.query(User).filter(
        User.id == stored_token.user_id
    ).first()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is unavailable",
        )

    # Rotate the refresh token so the old one cannot be reused.
    stored_token.revoked = True
    raw_refresh_token = create_refresh_token()

    new_token = RefreshToken(
        token_hash=hash_refresh_token(raw_refresh_token),
        user_id=user.id,
        expires_at=get_refresh_expiry(),
    )

    db.add(new_token)

    try:
        db.flush()

        response = {
            "access_token": create_access_token(user.id, user.role),
            "refresh_token": raw_refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

        db.commit()
        return response

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not refresh the session",
        )


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


# Example of server-side role-based access control.
# We can add dedicated administration routes later.
@router.get("/admin-check")
def admin_check(
    current_user: User = Depends(
        require_roles("administrator")
    ),
):
    return {
        "message": "Administrator access granted",
        "user_id": current_user.id,
        "role": current_user.role,
    }


@router.get("/inventory-manager-check")
def inventory_manager_check(
    current_user: User = Depends(
        require_roles("inventory_manager", "administrator")
    ),
):
    return {
        "message": "Inventory management access granted",
        "user_id": current_user.id,
        "role": current_user.role,
    }
# --------------------------------------------------
# GET ALL CUSTOMERS (ADMIN ONLY)
# --------------------------------------------------

@router.get(
    "/admin/customers",
    response_model=list[UserResponse],
)
def get_all_customers(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("administrator")
    ),
):
    customers = (
        db.query(User)
        .filter(User.role == "customer")
        .order_by(User.id.desc())
        .all()
    )

    return customers