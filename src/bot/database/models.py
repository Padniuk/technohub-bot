from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()

class Application(Base):
    __tablename__ = 'main_application'

    id = Column(Integer, primary_key=True)
    application_type = Column(String(30))
    name = Column(String(30))
    phone = Column(String(13))
    problem = Column(Text)
    address = Column(String(50))
    post_time = Column(DateTime, default=func.now())
    complete_time = Column(DateTime, nullable=True)
    message_id = Column(String(50))
    price = Column(Integer, default=0)
    act_id = Column(Integer, default=0)

    workers = relationship('Worker', secondary='main_applicationworkerassociation', back_populates='applications')#, lazy='dynamic'


class Worker(Base):
    __tablename__ = 'main_worker'

    id = Column(Integer, primary_key=True)
    worker_type = Column(String(30))
    name = Column(String(255))
    phone = Column(String(20))
    user_id = Column(String(50))
    additional_info = Column(Text)

    applications = relationship('Application', secondary='main_applicationworkerassociation', back_populates='workers')




class ApplicationWorkerAssociation(Base):
    __tablename__ = 'main_applicationworkerassociation'

    application_id = Column(Integer, ForeignKey('main_application.id'), primary_key=True)
    worker_id = Column(Integer, ForeignKey('main_worker.id'), primary_key=True)
    status = Column(String(50))
    comment = Column(String(255))