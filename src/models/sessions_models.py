from sqlalchemy import Column, Integer, String
from database import Base

class Sessions(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, index=True)
    stack = Column(String)
    user = Column(String, nullable=True)  # Assuming user can be nullable
