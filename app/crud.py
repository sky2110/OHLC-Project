from sqlalchemy.orm import Session
from sqlalchemy import text
from app import models
from datetime import datetime

def create_tick(db: Session, tick: models.Tick):
    db.add(tick)
    db.commit()
    db.refresh(tick)
    return tick

def get_ohlc(db: Session, timeframe: str, symbol: str, start_time: datetime, end_time: datetime):
    # Mapping timeframe to view
    view_map = {
        '1m': 'ohlc_1m',
        '1h': 'ohlc_1h',
        '1d': 'ohlc_1d',
        '1d_custom': 'ohlc_1d_custom_10pm' # Custom 10 PM view
    }
    
    if timeframe not in view_map:
        raise ValueError("Invalid timeframe. Use 1m, 1h, 1d, or 1d_custom")
        
    table_name = view_map[timeframe]
    
    # Using raw SQL for the view query as it's cleaner than mapping Aggregates to ORM
    # Note: 'bucket' in views corresponds to the time column
    
    # Use text() for safe parameter binding
    query = text(f"""
        SELECT bucket, open, high, low, close 
        FROM {table_name}
        WHERE symbol = :symbol 
        AND bucket >= :start_time 
        AND bucket < :end_time
        ORDER BY bucket ASC
    """)
    
    result = db.execute(query, {
        'symbol': symbol, 
        'start_time': start_time, 
        'end_time': end_time
    })
    
    return [
        {
            "time": row.bucket,
            "open": row.open,
            "high": row.high,
            "low": row.low,
            "close": row.close
        }
        for row in result
    ]
