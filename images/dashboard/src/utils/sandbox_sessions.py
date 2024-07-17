from fastapi import HTTPException
from sqlalchemy.orm import Session
from models import sessions
from sqlalchemy.exc import IntegrityError
from models.sessions import Sessions


def model_to_dict(model):
    """Convert sqlalchemy model to dict"""
    return {column.name: getattr(model, column.name) for column in model.__table__.columns}


def save_update_stack_session(db: Session, cookie_id: str, stack: str):
    """Save or update session and stack name

    Args:
        db (Session): database session
        cookie_id (str): cookie unique identifier
        stack (str): stack name
    """
    try:
        db_session = db.query(sessions.Sessions).filter_by(id=cookie_id).first()
        if db_session:
            db_session.stack = stack
        else:
            db_session = sessions.Sessions(id=cookie_id, stack=stack)
            db.add(db_session)
        db.commit()
        db.refresh(db_session)
        return db_session

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save or update session.")


def update_user_session(db: Session, cookie_id: str, user: str):
    """Update session user

    Args:
        db (Session): database session
        cookie_id (str): cookie unique identifier
    """
    db_session = db.query(Sessions).filter(Sessions.id == cookie_id).first()
    if db_session:
        db_session.user = user
        db.commit()
        db.refresh(db_session)
        return model_to_dict(db_session)
    else:
        raise ValueError(f"Session with id {cookie_id} does not exist")
