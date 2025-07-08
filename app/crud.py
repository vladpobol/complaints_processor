from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional

from app import models, schemas, external


async def create_complaint(db: Session, complaint_in: schemas.ComplaintCreate) -> models.Complaint:
    # Analyze sentiment
    sentiment = await external.analyze_sentiment(complaint_in.text)
    # Create initial complaint
    db_obj = models.Complaint(text=complaint_in.text, sentiment=sentiment)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    # Determine category (done after DB commit to have ID)
    category = await external.categorize_complaint(complaint_in.text)
    db_obj.category = category
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_complaints(
    db: Session,
    status: Optional[str] = None,
    from_seconds_ago: Optional[int] = None,
) -> List[models.Complaint]:
    q = db.query(models.Complaint)
    if status:
        q = q.filter(models.Complaint.status == status)
    if from_seconds_ago:
        cutoff = datetime.utcnow() - timedelta(seconds=from_seconds_ago)
        q = q.filter(models.Complaint.timestamp >= cutoff)
    return q.order_by(models.Complaint.timestamp.desc()).all()


def update_complaint_status(db: Session, complaint_id: int, status: str) -> Optional[models.Complaint]:
    """Update status of complaint. Accepts 'open' or 'closed'."""
    obj = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not obj:
        return None
    obj.status = status  # type: ignore
    db.commit()
    db.refresh(obj)
    return obj 