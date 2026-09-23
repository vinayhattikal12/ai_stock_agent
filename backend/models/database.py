import os
from datetime import datetime, date
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.config import settings

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# SQLite or PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DBHolding(Base):
    __tablename__ = "holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    buy_price = Column(Float, nullable=False)
    purchase_date = Column(Date, nullable=False, default=date.today)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DBSignalAudit(Base):
    __tablename__ = "signal_audits"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    signal = Column(String(50), nullable=False)
    entry_low = Column(Float, nullable=False)
    entry_high = Column(Float, nullable=False)
    target_1 = Column(Float, nullable=False)
    target_2 = Column(Float, nullable=False)
    target_3 = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    probability_t1 = Column(Float, nullable=False)
    market_regime = Column(String(50), nullable=False)
    sector = Column(String(50), nullable=False)
    setup_type = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    holding_days_max = Column(Integer, default=10)
    outcome_status = Column(String(50), default="ACTIVE") # ACTIVE, T1_HIT, T2_HIT, T3_HIT, STOP_HIT, EXPIRED
    mfe_pct = Column(Float, default=0.0) # Max Favorable Excursion
    mae_pct = Column(Float, default=0.0) # Max Adverse Excursion
    actual_holding_days = Column(Integer, nullable=True)
    return_pct = Column(Float, nullable=True)
    reasoning_json = Column(Text, nullable=True)

class DBCacheEntry(Base):
    __tablename__ = "cache_entries"
    
    key = Column(String(255), primary_key=True, index=True)
    value = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)

class DBInstrumentMaster(Base):
    __tablename__ = "instrument_master"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    sector = Column(String(100), nullable=False)
    instrument_key = Column(String(100), nullable=False)
    market_cap_category = Column(String(50), nullable=False, index=True) # LARGE_CAP, MID_CAP, SMALL_CAP
    market_cap_rank = Column(Integer, nullable=True, index=True) # 1-100 Large, 101-250 Mid, 251+ Small
    classification_source = Column(String(100), default="SEBI/AMFI Semiannual Framework")
    classification_date = Column(Date, default=date.today)
    is_active = Column(Boolean, default=True)
    last_refreshed_at = Column(DateTime, default=datetime.utcnow)

class DBHistoricalScan(Base):
    __tablename__ = "historical_scans"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    market_regime = Column(String(50), nullable=False)
    total_qualified_count = Column(Integer, default=0)
    large_cap_count = Column(Integer, default=0)
    mid_cap_count = Column(Integer, default=0)
    small_cap_count = Column(Integer, default=0)
    total_scanned = Column(Integer, default=0)
    top_symbols_json = Column(Text, nullable=True)
    result_json = Column(Text, nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)
    # Lazy import to avoid circular dependency
    try:
        from backend.services.market_data.universe import seed_instrument_master_if_empty
        db = SessionLocal()
        try:
            seed_instrument_master_if_empty(db)
        finally:
            db.close()
    except Exception as e:
        print(f"Error seeding instrument master: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

