from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import BaseModel


class User(BaseModel):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True)
    username      = Column(String(50), unique=True, nullable=False)
    email         = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role          = Column(String(20), default="user")
    created_at    = Column(DateTime, server_default=func.now())
    last_login    = Column(DateTime)
    searches      = relationship("Search", back_populates="user")
    feedbacks     = relationship("Feedback", back_populates="user")


class ApiKey(BaseModel):
    __tablename__ = "api_keys"
    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    key_hash   = Column(String(255), nullable=False)
    name       = Column(String(100))
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime)


class Source(BaseModel):
    __tablename__ = "sources"
    id           = Column(Integer, primary_key=True)
    name         = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100))
    base_url     = Column(String(255))
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime, server_default=func.now())


class Search(BaseModel):
    __tablename__ = "searches"
    id              = Column(Integer, primary_key=True)
    user_id         = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    source_id       = Column(Integer, ForeignKey("sources.id"))
    keyword         = Column(String(255), nullable=False)
    limit_requested = Column(Integer, default=10)
    results_count   = Column(Integer, default=0)
    status          = Column(String(20), default="pending")
    error_message   = Column(Text)
    created_at      = Column(DateTime, server_default=func.now())
    completed_at    = Column(DateTime)
    user            = relationship("User", back_populates="searches")
    predictions     = relationship("Prediction", back_populates="search",
                                   cascade="all, delete-orphan")


class Prediction(BaseModel):
    __tablename__ = "predictions"
    id              = Column(Integer, primary_key=True)
    search_id       = Column(Integer, ForeignKey("searches.id", ondelete="CASCADE"))
    source_id       = Column(Integer, ForeignKey("sources.id"))
    text            = Column(Text, nullable=False)
    sentiment       = Column(String(20))
    sentiment_score = Column(Float)          # ancien "confidence"
    language        = Column(String(10), default="multi")
    metadata_json   = Column(JSON)
    created_at      = Column(DateTime, server_default=func.now())
    search          = relationship("Search", back_populates="predictions")
    feedbacks       = relationship("Feedback", back_populates="prediction")


class Feedback(BaseModel):
    __tablename__ = "feedbacks"
    id            = Column(Integer, primary_key=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id", ondelete="CASCADE"))
    user_id       = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    is_correct    = Column(Boolean, nullable=False)
    comment       = Column(Text)
    created_at    = Column(DateTime, server_default=func.now())
    prediction    = relationship("Prediction", back_populates="feedbacks")
    user          = relationship("User", back_populates="feedbacks")