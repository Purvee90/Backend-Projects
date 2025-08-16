from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime, timezone
from database import Base
import pytz

IST = pytz.timezone("Asia/Kolkata")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(IST))

    urls = relationship("URL", back_populates="owner")


class URL(Base):
    __tablename__ = "urls"
    id = Column(Integer, primary_key=True, index=True)
    long_url = Column(String, nullable=False)
    short_code = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(IST))
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", back_populates="urls")
    clicks = relationship("Click", back_populates="url")

    @property
    def status(self):
        """Get the current status of the URL"""
        if isinstance(self.is_active, Column):
            is_active = bool(self.is_active.scalar())
        else:
            is_active = bool(self.is_active)

        if not is_active:
            return "inactive"

        expires_at = self.expires_at
        if isinstance(expires_at, Column):
            expires_at = expires_at.scalar()

        # Convert expiry time to IST if it's not None and has no timezone
        if expires_at and expires_at.tzinfo is None:
            expires_at = IST.localize(expires_at)

        current_time = datetime.now(IST)
        if expires_at and expires_at < current_time:
            return "expired"

        return "active"

    @property
    def is_expired(self):
        """Check if URL is expired"""
        expires_at = self.expires_at
        if isinstance(expires_at, Column):
            expires_at = expires_at.scalar()

        if expires_at is None:
            return False

        # Convert expiry time to IST if it's not None and has no timezone
        if expires_at.tzinfo is None:
            expires_at = IST.localize(expires_at)

        current_time = datetime.now(IST)
        return expires_at < current_time


class Click(Base):
    __tablename__ = "clicks"
    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey("urls.id"))
    timestamp = Column(DateTime, default=lambda: datetime.now(IST))
    ip_address = Column(String)
    user_agent = Column(String)

    url = relationship("URL", back_populates="clicks")
