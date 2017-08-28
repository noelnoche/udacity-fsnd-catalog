"""
This module contains setup code for interacting with the database.

"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from catalog.db_setup import Base

engine = create_engine("sqlite:///catalog/catalog.db")
Base.metadata.create_all(bind=engine)
session_factory = sessionmaker(bind=engine)
DBSession = scoped_session(session_factory)
