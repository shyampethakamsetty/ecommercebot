from app.models.base import Base
from app.models.models import *
from app.deps import engine, SessionLocal
from sqlalchemy.orm import Session
from datetime import datetime

def create_tables_and_seed_data():
    print('Creating tables...')
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print('Tables created successfully.')
    
    # Create seed data
    print('Creating seed data...')
    db = SessionLocal()
    
    try:
        # Create default user if it doesn't exist
        default_user = db.query(User).filter(User.id == 1).first()
        if not default_user:
            default_user = User(
                id=1,
                email="default@botmart.com",
                hashed_password="dummy_hash",
                created_at=datetime.utcnow()
            )
            db.add(default_user)
            print('Created default user.')
        else:
            print('Default user already exists.')
        
        # Create default workflow if it doesn't exist
        default_workflow = db.query(Workflow).filter(Workflow.id == 1).first()
        if not default_workflow:
            default_workflow = Workflow(
                id=1,
                name="Default Search Workflow",
                owner_id=1,
                definition={},
                enabled=True,
                created_at=datetime.utcnow()
            )
            db.add(default_workflow)
            print('Created default workflow.')
        else:
            print('Default workflow already exists.')
        
        # Commit changes
        db.commit()
        print('Seed data created successfully.')
        
    except Exception as e:
        print(f'Error creating seed data: {e}')
        db.rollback()
        raise
    finally:
        db.close()
    
    print('Database initialization completed!')

if __name__ == "__main__":
    create_tables_and_seed_data()
