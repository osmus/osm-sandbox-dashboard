from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class UserRole(enum.Enum):
    ADMIN = "admin"
    CREATOR = "creator"
    USER = "user"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    osm_id = Column(Integer, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
