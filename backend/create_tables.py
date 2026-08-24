from backend.database import engine
from backend.models import Base

Base.metadata.create_all(engine)

print("Database tables created!")