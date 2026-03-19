import os
import bcrypt
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.exc import IntegrityError

try:
    # Try to get DB URL from Streamlit secrets (for Cloud deployment)
    DB_URL = st.secrets.get("DATABASE_URL", None)
except Exception:
    DB_URL = None

if not DB_URL:
    # Fallback to local env var or SQLite
    DB_URL = os.environ.get("DATABASE_URL", "sqlite:///expense_tracker.db")

# Some SQLAlchemy URIs need 'postgresql://' instead of 'postgres://'
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs multi-thread check disabled for scoped sessions in web apps often
if DB_URL.startswith("sqlite"):
    engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DB_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    
    # Relationships
    members = relationship("FamilyMember", back_populates="user", cascade="all, delete")
    expenses = relationship("Expense", back_populates="user", cascade="all, delete")

class FamilyMember(Base):
    __tablename__ = "family_members"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    earning_status = Column(Boolean, nullable=False)
    earnings = Column(Float, nullable=False)
    
    user = relationship("User", back_populates="members")

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String, nullable=False)
    description = Column(String, nullable=True)
    value = Column(Float, nullable=False)
    date = Column(String, nullable=False)

    user = relationship("User", back_populates="expenses")

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed admin account
    db = SessionLocal()
    admin = db.query(User).filter(User.username == 'admin').first()
    if not admin:
        admin_pass = hash_password('admin123')
        admin_user = User(username='admin', password_hash=admin_pass)
        db.add(admin_user)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
    db.close()

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_user(username, password):
    db = SessionLocal()
    try:
        new_user = User(username=username, password_hash=hash_password(password))
        db.add(new_user)
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False
    finally:
        db.close()

def authenticate_user(username, password):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    
    if user and verify_password(password, user.password_hash):
        return {"id": user.id, "username": user.username}
    return None

def get_all_users():
    db = SessionLocal()
    users = db.query(User).all()
    db.close()
    return [(u.id, u.username) for u in users]

def get_all_members():
    db = SessionLocal()
    members = db.query(FamilyMember).join(User).all()
    rows = [(m.id, m.user.username, m.name, m.earning_status, m.earnings) for m in members]
    db.close()
    return rows

def get_all_expenses():
    db = SessionLocal()
    expenses = db.query(Expense).join(User).all()
    rows = [(e.id, e.user.username, e.category, e.description, e.value, e.date) for e in expenses]
    db.close()
    return rows

init_db()
