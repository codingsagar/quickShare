from sqlmodel import Field, SQLModel, create_engine,Session
import os
from datetime import datetime
from typing import Optional,Generator


class File(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, nullable=False)  
    url: str = Field(nullable=False) 
    uploaded_at: datetime = Field(default_factory=datetime.now) 
    downloaded: bool = Field(default=False) 


DATABASE_URL = f"postgresql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOSTNAME')}:{os.getenv('DB_PORT')}/quickshare"

engine = create_engine(DATABASE_URL, echo=True)

def db_init():
    try:
        SQLModel.metadata.create_all(engine)
        print("Tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session 