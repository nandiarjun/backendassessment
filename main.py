from fastapi import FastAPI, Depends, BackgroundTasks, status
from sqlalchemy.orm import Session
from datetime import datetime
from database import engine, SessionLocal
import models
from schemas import TransactionWebhook
import time

app = FastAPI(title="Fullstack Engineer Assessment API")

# Create tables
models.Base.metadata.create_all(bind=engine)


# Dependency to get DB session (request-scoped)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------
# Health Check API
# -------------------------
@app.get("/")
def health_check():
    return {
        "status": "HEALTHY",
        "current_time": datetime.utcnow().isoformat()
    }


# -------------------------
# Background Processing
# -------------------------
def process_transaction(transaction_id: str):
    """
    Background job:
    - Creates its own DB session
    - Waits 30 seconds
    - Marks transaction as PROCESSED
    """
    db = SessionLocal()
    try:
        time.sleep(30)  # simulate external API call

        transaction = db.query(models.Transaction).filter(
            models.Transaction.transaction_id == transaction_id
        ).first()

        if transaction:
            transaction.status = "PROCESSED"
            transaction.processed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


# -------------------------
# Webhook Endpoint
# -------------------------
@app.post("/v1/webhooks/transactions", status_code=status.HTTP_202_ACCEPTED)
def receive_transaction(
    payload: TransactionWebhook,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Receives transaction webhook.
    Responds immediately with 202.
    Ensures idempotency using transaction_id.
    """

    existing = db.query(models.Transaction).filter(
        models.Transaction.transaction_id == payload.transaction_id
    ).first()

    if not existing:
        transaction = models.Transaction(
            transaction_id=payload.transaction_id,
            source_account=payload.source_account,
            destination_account=payload.destination_account,
            amount=payload.amount,
            currency=payload.currency,
            status="PROCESSING",
            created_at=datetime.utcnow()
        )
        db.add(transaction)
        db.commit()

        # Start background task WITHOUT passing DB session
        background_tasks.add_task(process_transaction, payload.transaction_id)

    return {"message": "Accepted"}


# -------------------------
# Transaction Status API
# -------------------------
@app.get("/v1/transactions/{transaction_id}")
def get_transaction_status(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    transaction = db.query(models.Transaction).filter(
        models.Transaction.transaction_id == transaction_id
    ).first()

    if not transaction:
        return {"message": "Transaction not found"}

    return {
        "transaction_id": transaction.transaction_id,
        "source_account": transaction.source_account,
        "destination_account": transaction.destination_account,
        "amount": float(transaction.amount),
        "currency": transaction.currency,
        "status": transaction.status,
        "created_at": transaction.created_at,
        "processed_at": transaction.processed_at
    }
