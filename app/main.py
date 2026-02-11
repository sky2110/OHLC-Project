from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app import models, database, crud

# Create tables (if using ORM to create, though schema.sql is preferred for TimescaleDB)
# models.Base.metadata.create_all(bind=database.engine)
# Note: We rely on schema.sql because SQLAlchemy doesn't natively support hypertable creation smoothly without custom DDL

app = FastAPI(title="Real-time FX OHLC", version="1.0.0")

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Schemas
class TickCreate(BaseModel):
    symbol: str
    price: float
    timestamp: Optional[datetime] = None

class OHLCResponse(BaseModel):
    time: datetime
    open: float
    high: float
    low: float
    close: float

@app.get('/health')
def health_check():
    return {'status': 'ok', 'service': 'fx-ohlc'}

@app.post("/ticks", status_code=201)
def ingest_tick(tick: TickCreate, db: Session = Depends(get_db)):
    """
    Ingest a new market tick. 
    Timestamp is optional, defaults to now() if not provided (handled by DB or app).
    """
    if not tick.timestamp:
        tick.timestamp = datetime.now()
        
    db_tick = models.Tick(
        symbol=tick.symbol,
        price=tick.price,
        timestamp=tick.timestamp
    )
    return crud.create_tick(db=db, tick=db_tick)

@app.get("/ohlc/{timeframe}", response_model=List[OHLCResponse])
def get_ohlc_data(
    timeframe: str,
    symbol: str = Query(..., description="Currency pair symbol, e.g., EURUSD"),
    from_time: datetime = Query(..., alias="from"),
    to_time: datetime = Query(..., alias="to"),
    db: Session = Depends(get_db)
):
    """
    Get OHLC data for a specific timeframe.
    Supported timeframes: 1m, 1h, 1d, 1d_custom (10PM-10PM)
    """
    try:
        data = crud.get_ohlc(db, timeframe, symbol, from_time, to_time)
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
