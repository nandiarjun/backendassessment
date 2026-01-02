from sqlalchemy import Column, Integer, String, Numeric, DateTime
from datetime import datetime
from database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True)
    source_account = Column(String)
    destination_account = Column(String)
    amount = Column(Numeric)
    currency = Column(String, default="INR")
    status = Column(String, default="PROCESSING")  # PROCESSING or PROCESSED
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    class Config:
        from_attributes = True
