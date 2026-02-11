from sqlalchemy import Column, Float, String, DateTime
from app.database import Base

class Tick(Base):
    __tablename__ = 'ticks'
    
    # TimescaleDB requires the time column to be part of the primary key if there is one,
    # or no primary key. SQLAlchemy usually wants a PK.
    # We can use a composite PK of (timestamp, symbol) for now, 
    # though strictly in high-throughput timeseries we might drop PK enforcement in app 
    # and rely on DB.
    
    timestamp = Column(DateTime(timezone=True), primary_key=True)
    symbol = Column(String, primary_key=True)
    price = Column(Float)
    
# We don't necessarily need ORM models for the views if we use raw SQL or Pydantic for read.
