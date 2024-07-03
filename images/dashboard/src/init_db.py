from database import SessionLocal, engine, Base
from models.resources import Resources


def init_db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    resource1 = Resources(
        label="t3-medium-ondemand", inst_cpu="2", inst_ram="4Gi", max_inst_allowed=10
    )
    resource2 = Resources(
        label="t3-large-ondemand", inst_cpu="2", inst_ram="8Gi", max_inst_allowed=10
    )
    session.add(resource1)
    session.add(resource2)
    session.commit()
    session.close()


init_db()
