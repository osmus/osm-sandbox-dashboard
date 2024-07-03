from database import SessionLocal, engine, Base
from models.resources import Resources


def init_db():
    # Create the resources table if it doesn't exist
    Base.metadata.create_all(bind=engine)

    # Create a session
    session = SessionLocal()

    # Create instances of your Resources model
    resource1 = Resources(label="t3-medium-ondemand", cpu=2, ram=4)
    resource2 = Resources(label="t3-large-ondemand", cpu=2, ram=8)

    # Add instances to the session
    session.add(resource1)
    session.add(resource2)

    # Commit the session to save changes
    session.commit()

    # Close the session
    session.close()

init_db()