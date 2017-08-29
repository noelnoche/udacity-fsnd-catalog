#!/usr/bin/env python

"""
This script sets up and builds the database tables and should be
executed first before running the application.
Run the following command from the applicaiton root directory:

    python catalog/db_setup.py

"""

import random
import string
from sqlalchemy import (Boolean, Column, create_engine, DateTime, ForeignKey,
                        Integer, String)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Used for hashing passwords
from passlib.apps import custom_app_context as pwd_context


# Used for generating cryptographically signed messages (tokens)
# https://www.tutorialspoint.com/cryptography/cryptography_digital_signatures.htm
from itsdangerous import(TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
secret_key = "".join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))


Base = declarative_base()


class User(Base):
    """Class for a User record."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    password_hash = Column(String(250), nullable=False, default=False)
    picture = Column(String(250), nullable=True)
    public = Column(Boolean, nullable=False, default=True)
    items = relationship("Item", backref="owner", lazy="dynamic")
    categories = relationship("Category", backref="owner", lazy="dynamic")
    def hash_password(self, password):
        """Hashes password during registration"""

        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        """Called when user needs credentials validated"""

        return pwd_context.verify(password, self.password_hash)

    # def generate_auth_token(self, expiration=600):
    #     """Serializer encrypts to hide the id of the user"""

    #     ser = Serializer(secret_key, expires_in=expiration)

    #     return ser.dumps({"id":self.id})

    @staticmethod
    def verify_auth_token(token):
        """Validates tokens made by `generate_auth_token()`"""

        ser = Serializer(secret_key)

        try:
            data = ser.loads(token)
        except SignatureExpired:
            return None
        except BadSignature:
            return None
        user_id = data["id"]
        return user_id


class Category(Base):
    """Class for a Category record."""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    user_id_rel = relationship("User")

    @property
    def serialize(self):
        """Retruns serialized data for RESTful API feature."""

        return {
            "id": self.id,
            "name": self.name,
            "user_id": self.user_id
        }


class Item(Base):
    """Class for an Item record."""

    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False, default="No title")
    description = Column(String(250), default="No description provided.")
    image_file = Column(String(250), nullable=True, default=None)
    image_url = Column(String(250), nullable=True, default=None)
    create_date = Column(DateTime, default=func.now())
    category_name = Column(String(80), ForeignKey("categories.name"), default="Unsorted")
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey("users.id"))
    user_id_rel = relationship("User")

    @property
    def serialize(self):
        """Retruns serialized data for RESTful API feature."""

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "image_url": self.image_url,
            "category": self.category_name,
            "user_id": self.user_id
        }

# ----------------------------------------------------------------------

engine = create_engine("sqlite:///catalog/catalog.db")
Base.metadata.create_all(engine)
