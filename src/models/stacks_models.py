from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Stacks(Base):
    __tablename__ = "stacks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    status = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
