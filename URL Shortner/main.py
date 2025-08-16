from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, update
from database import SessionLocal, engine
from models import Base, URL, Click, User
from utils import generate_unique_short_code, validate_custom_code
from cache import Cache
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware
import qrcode
import io
import base64
import pytz
import asyncio

# Set timezone to IST
IST = pytz.timezone("Asia/Kolkata")

# Import environment variables
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Security
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set in environment variables")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

Base.metadata.create_all(bind=engine)
app = FastAPI()


async def update_expired_urls():
    """Background task to update is_active status of expired URLs"""
    while True:
        db = None
        try:
            db = SessionLocal()
            current_time = datetime.now(IST)

            # Update is_active status for expired URLs in a single query
            stmt = (
                update(URL)
                .where(
                    and_(
                        URL.is_active.is_(True),
                        URL.expires_at.isnot(None),
                        URL.expires_at < current_time,
                    )
                )
                .values(is_active=False)
            )

            db.execute(stmt)
            db.commit()

        except Exception as e:
            print(f"Error in update_expired_urls: {e}")
        finally:
            if db:
                db.close()

        # Wait for 5 minutes before next check
        await asyncio.sleep(300)


@app.on_event("startup")
async def start_background_tasks():
    """Start background tasks when the application starts"""
    background_tasks = BackgroundTasks()
    background_tasks.add_task(update_expired_urls)


# Cache setup
cache = Cache(Cache.MEMORY)


class Token(BaseModel):
    access_token: str
    token_type: str


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True  # newer version of orm_mode


class URLRequest(BaseModel):
    long_url: str
    expires_at: datetime | None = None  # Optional expiry
    custom_code: str | None = None  # Optional custom short code
    expiry_minutes: int | None = None  # Expiry in minutes


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    current_time = datetime.now(IST)
    if expires_delta:
        expire = current_time + expires_delta
    else:
        expire = current_time + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not isinstance(username, str):
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


@app.post("/register")
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username exists
    if db.query(User).filter(User.username == user.username).count() > 0:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        hashed_password=hashed_password,
        is_active=True,
    )
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
        return {"message": "User created successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")


@app.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/shorten")
async def shorten_url(
    request: URLRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Handle custom short code if provided
    if request.custom_code:
        if not validate_custom_code(request.custom_code):
            raise HTTPException(status_code=400, detail="Invalid custom code format")
        if db.query(URL).filter(URL.short_code == request.custom_code).first():
            raise HTTPException(status_code=400, detail="Custom code already exists")
        short_code = request.custom_code
    else:
        short_code = generate_unique_short_code(db)

    # Handle expiration time
    expires_at = None
    current_time = datetime.now(IST)

    if request.expiry_minutes:
        # Convert minutes to timedelta and add to current IST time
        expires_at = current_time + timedelta(minutes=int(request.expiry_minutes))
    elif request.expires_at:
        # Ensure the provided expires_at is in IST
        if request.expires_at.tzinfo is None:
            expires_at = IST.localize(request.expires_at)
        else:
            expires_at = request.expires_at.astimezone(IST)

    db_url = URL(
        long_url=request.long_url,
        short_code=short_code,
        expires_at=expires_at,
        is_active=True,
        owner_id=current_user.id,
    )
    db.add(db_url)
    db.commit()
    db.refresh(db_url)

    # Cache the URL
    await cache.set(short_code, request.long_url)

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"http://localhost:8000/{short_code}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert QR code to base64
    buffered = io.BytesIO()
    img.save(buffered)  # PIL will auto-detect format
    qr_code = base64.b64encode(buffered.getvalue()).decode()

    return {
        "short_url": f"http://localhost:8000/{short_code}",
        "qr_code": qr_code,
        "expires_at": expires_at,
    }


@app.get("/{short_code}")
async def redirect(short_code: str, request: Request, db: Session = Depends(get_db)):
    # First, try to get the URL from database
    db_url = db.query(URL).filter(URL.short_code == short_code).first()
    if db_url is None:
        raise HTTPException(status_code=404, detail="URL not found")

    # Check if URL is expired and update is_active if needed
    status = db_url.status
    if status == "expired":
        # Update the is_active status in the database
        db.query(URL).filter(URL.id == db_url.id).update({"is_active": False})
        db.commit()
        raise HTTPException(status_code=410, detail="URL is expired")
    elif status != "active":
        raise HTTPException(status_code=410, detail=f"URL is {status}")

    # Try to get the long URL from cache
    long_url = await cache.get(short_code)
    if not long_url:
        long_url = db_url.long_url
        await cache.set(short_code, long_url)

    # Track click
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    click = Click(
        url_id=db_url.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(click)
    db.commit()

    return RedirectResponse(url=str(long_url), status_code=307)


@app.get("/analytics/{short_code}")
async def get_analytics(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_url = db.query(URL).filter(URL.short_code == short_code).first()
    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")

    # Check if user owns this URL or is admin
    if (
        not db.query(URL)
        .filter(URL.id == db_url.id, URL.owner_id == current_user.id)
        .first()
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to view these analytics"
        )

    # Get basic click count
    click_count = db.query(Click).filter(Click.url_id == db_url.id).count()

    # Get clicks by time periods
    now = datetime.now(IST)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    daily_clicks = (
        db.query(Click)
        .filter(and_(Click.url_id == db_url.id, Click.timestamp >= day_ago))
        .count()
    )

    weekly_clicks = (
        db.query(Click)
        .filter(and_(Click.url_id == db_url.id, Click.timestamp >= week_ago))
        .count()
    )

    monthly_clicks = (
        db.query(Click)
        .filter(and_(Click.url_id == db_url.id, Click.timestamp >= month_ago))
        .count()
    )

    # Get unique visitors (by IP)
    unique_visitors = (
        db.query(Click.ip_address).filter(Click.url_id == db_url.id).distinct().count()
    )

    # Get top user agents
    top_browsers = (
        db.query(Click.user_agent, func.count(Click.id).label("count"))
        .filter(Click.url_id == db_url.id)
        .group_by(Click.user_agent)
        .order_by(func.count(Click.id).desc())
        .limit(5)
        .all()
    )

    return {
        "long_url": db_url.long_url,
        "created_at": db_url.created_at,
        "expires_at": db_url.expires_at,
        "is_active": db_url.is_active,
        "status": db_url.status,
        "analytics": {
            "total_clicks": click_count,
            "last_24h_clicks": daily_clicks,
            "last_7d_clicks": weekly_clicks,
            "last_30d_clicks": monthly_clicks,
            "unique_visitors": unique_visitors,
            "top_browsers": [
                {"browser": ua, "clicks": count} for ua, count in top_browsers
            ],
        },
    }


# uvicorn main:app --reload
