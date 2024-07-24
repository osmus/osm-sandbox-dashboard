from sqlalchemy import Column, String, Integer
from database import Base


class Resources(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    label = Column(String, unique=True)
    inst_cpu = Column(String)
    inst_ram = Column(String)
    max_inst_allowed = Column(Integer)
