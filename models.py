from sqlalchemy import String, Column, Integer, DateTime, Boolean, Enum, func
from sqlalchemy.orm import DeclarativeBase, declarative_base
from sqlalchemy.exc import IntegrityError
import enum
# from src.database import Session
from database import Session
from datetime import datetime

session = Session()

Base = declarative_base()

class BaseModel(Base):

    __abstract__ = True # __abstract__ directive is used for abstract classes that should not be mapped to a database table

    # These times are stored as UTC 
    # create_time = Column(DateTime(timezone=True), server_default=str(datetime.now())) 
    # update_time = Column(DateTime(timezone=True), server_default=func.now())


    ''' Alterações no banco de dados '''

    def save(self):
        session.add(self)
        try:
            session.commit()
        except IntegrityError as err:
            session.rollback()
            
    def update(self):
        try:
            session.commit()
        except IntegrityError as err:
            session.rollback()
    
    def delete(self):
        session.delete(self)
        try:
            session.commit()
        except IntegrityError as err:
            session.rollback()

class CarpoolType(enum.Enum):
    going = 'going'
    returning = 'returning'

class Carpool(BaseModel):
    __tablename__ = 'carpool'

    id: int = Column(Integer, primary_key=True)
    
    chat_id: str = Column(String(100)) # Not a FK

    created_at: DateTime = Column(DateTime(timezone=False))
    departure_datetime: DateTime = Column(DateTime(timezone=False))
    telegram_username: str = Column(String(100))
    place: str = Column(String(100))
    available_seats: int = Column(Integer)
    is_active: bool = Column(Boolean)
    carpool_type: Enum = Column(Enum(CarpoolType))
