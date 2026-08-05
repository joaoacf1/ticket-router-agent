from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.ticket import DBTicket
from app.models.schemas import TicketCreate, TicketResponse
from app.agents.router import classify_ticket

router = APIRouter()

@router.post("/tickets", response_model=TicketResponse, status_code=201)
async def create_ticket(
    ticket_in: TicketCreate,
    db: AsyncSession = Depends(get_db)
):
    db_ticket = DBTicket(
        title=ticket_in.title,
        description=ticket_in.description
    )
    db.add(db_ticket)
    await db.commit()
    await db.refresh(db_ticket)
    
    try:
        classification = await classify_ticket({
            "id": db_ticket.id,
            "title": db_ticket.title,
            "description": db_ticket.description
        })
        if classification.confidence >= 0.6:
            db_ticket.status = "routed"
            db_ticket.department = classification.department
            db_ticket.confidence = classification.confidence
        else:
            db_ticket.status = "pending_review"
            db_ticket.department = None
            db_ticket.confidence = classification.confidence
    except Exception:
        db_ticket.status = "pending_review"
        db_ticket.department = None
        
    await db.commit()
    await db.refresh(db_ticket)
    return db_ticket

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/tickets/pending-review", response_model=list[TicketResponse])
async def get_pending_review_tickets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DBTicket).where(DBTicket.status == "pending_review"))
    return result.scalars().all()
