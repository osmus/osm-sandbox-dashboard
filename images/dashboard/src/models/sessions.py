from sqlalchemy import Column, String, DateTime
from database import Base
from datetime import datetime


class Sessions(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, index=True)
    box = Column(String)
    end_redirect_uri = Column(String, nullable=True)
    user = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
