from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app import schemas, crud, models
from app.database import SessionLocal, init_db

# Ensure tables exist at startup
init_db()

app = FastAPI(title="Customer Complaints API")


# Dependency to provide DB session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/complaints", response_model=schemas.ComplaintResponse, status_code=status.HTTP_201_CREATED)
async def create_complaint(
    complaint_in: schemas.ComplaintCreate, db: Session = Depends(get_db)
):
    try:
        obj = await crud.create_complaint(db, complaint_in)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Internal error") from exc
    return obj


@app.get("/complaints", response_model=List[schemas.ComplaintResponse])
def list_complaints(
    status: Optional[schemas.StatusEnum] = None,
    from_timestamp: Optional[int] = None,
    db: Session = Depends(get_db),
):
    status_value = status.value if status else None
    objs = crud.get_complaints(db, status=status_value, from_seconds_ago=from_timestamp)
    return objs


@app.patch("/complaints/{complaint_id}", response_model=schemas.ComplaintResponse)
def update_complaint_status(
    complaint_id: int,
    update_in: schemas.ComplaintUpdate,
    db: Session = Depends(get_db),
):
    obj = crud.update_complaint_status(db, complaint_id, update_in.status.value)
    if not obj:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return obj 