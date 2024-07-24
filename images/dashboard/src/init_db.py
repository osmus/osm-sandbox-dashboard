from sqlalchemy.exc import IntegrityError
from database import SessionLocal, engine, Base
from models.resources import Resources


def init_db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    resources_to_add = [
        {"label": "t3-medium-ondemand", "inst_cpu": "2", "inst_ram": "4Gi", "max_inst_allowed": 10},
        {"label": "t3-large-ondemand", "inst_cpu": "2", "inst_ram": "8Gi", "max_inst_allowed": 10},
        {
            "label": "t3-xlarge-ondemand",
            "inst_cpu": "4",
            "inst_ram": "16Gi",
            "max_inst_allowed": 10,
        },
    ]

    for resource_data in resources_to_add:
        existing_resource = session.query(Resources).filter_by(label=resource_data["label"]).first()
        if existing_resource:
            # Update existing resource if needed
            existing_resource.inst_cpu = resource_data["inst_cpu"]
            existing_resource.inst_ram = resource_data["inst_ram"]
            existing_resource.max_inst_allowed = resource_data["max_inst_allowed"]
        else:
            # Add new resource
            new_resource = Resources(**resource_data)
            session.add(new_resource)

    try:
        session.commit()
    except IntegrityError as e:
        session.rollback()
        print(f"Error committing to the database: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    init_db()
