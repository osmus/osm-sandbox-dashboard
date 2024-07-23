from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from enum import Enum

Base = declarative_base()


class StateEnum(Enum):
    pending = "Pending"
    running = "Running"
    terminated = "Terminated"
    failure = "Failure"


class Boxes(Base):
    __tablename__ = "boxes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    subdomain = Column(String, nullable=False)
    resource_label = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    state = Column(SQLEnum(StateEnum), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    age = Column(Float, nullable=True)
