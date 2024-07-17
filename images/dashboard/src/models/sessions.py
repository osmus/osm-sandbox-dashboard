from sqlalchemy import Column, String
from database import Base


class Sessions(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, index=True)
    stack = Column(String)
    user = Column(String, nullable=True)
