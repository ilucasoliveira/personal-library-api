from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..auth import DUMMY_HASH, create_access_token, hash_password, verify_password
from ..config import ALLOW_SIGNUP, DEMO_MODE
from ..database import get_db
from ..errors import ApiError
from ..models import User
from ..ratelimit import client_ip, failed_logins, signups
from ..schemas import TokenResponse, UserCreate

router = APIRouter(prefix="/auth")


def token_for(user: User) -> TokenResponse:
    return TokenResponse(access_token=create_access_token(user), user=user)


@router.post("/register", status_code=201, response_model=TokenResponse)
def register(data: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Cria uma conta e já devolve o token de login."""
    if not ALLOW_SIGNUP:
        raise ApiError(403, "signup_disabled", "Sign up is disabled.")

    ip = client_ip(request)
    signups.check(ip)

    email = data.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise ApiError(409, "email_taken", "Email already registered.")

    user = User(
        email=email,
        name=data.name,
        password_hash=hash_password(data.password),
        language=data.language,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    signups.hit(ip)
    return token_for(user)


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Entra com email (no campo username) e senha. Formato de formulário, como o OAuth2 pede."""
    email = form.username.strip().lower()
    failed_logins.check(email)

    user = db.query(User).filter(User.email == email).first()
    password_ok = verify_password(form.password, user.password_hash if user else DUMMY_HASH)

    if user is None or not password_ok or user.is_visitor:
        failed_logins.hit(email)
        raise ApiError(
            401,
            "invalid_credentials",
            "Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    failed_logins.reset(email)
    return token_for(user)


@router.post("/visitor", response_model=TokenResponse)
def visitor_login(db: Session = Depends(get_db)):
    """Entra na conta compartilhada de visitante (só no deploy da demo)."""
    if not DEMO_MODE:
        raise ApiError(404, "not_found", "Not Found")

    visitor = db.query(User).filter(User.is_visitor.is_(True)).first()
    if visitor is None:
        raise ApiError(503, "demo_not_ready", "The demo account is not ready yet.")
    return token_for(visitor)
