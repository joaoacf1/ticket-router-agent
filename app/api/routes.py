from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.ticket import DBTicket
from app.models.schemas import TicketCreate, TicketResponse

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
    return db_ticket

@router.get("/health")
async def health_check():
    return {"status": "ok"}
