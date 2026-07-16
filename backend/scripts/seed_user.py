from app.db import SessionLocal, engine
from app.models import User, UserRole, Base
from app.core.security import get_password_hash

def seed():
    # Force drop and recreate all tables to ensure schema matches models exactly
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        user = User(
            username="admin",
            email="admin@phishingdetector.local",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.admin
        )
        db.add(user)
        db.commit()
        print("Admin user created successfully.")
    else:
        print("Admin user already exists.")
    
    analyst = db.query(User).filter(User.username == "analyst").first()
    if not analyst:
        analyst = User(
            username="analyst",
            email="analyst@phishingdetector.local",
            hashed_password=get_password_hash("analyst123"),
            role=UserRole.analyst
        )
        db.add(analyst)
        db.commit()
        print("Analyst user created successfully.")
    else:
        print("Analyst user already exists.")
        
    db.close()

if __name__ == "__main__":
    seed()
