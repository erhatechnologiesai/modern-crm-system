from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from app.database import get_db
from app.schemas import DealCreate, DealResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/deals", tags=["Deals"])

@router.get("", response_model=List[DealResponse])
def list_deals(
    stage: Optional[str] = None,
    company_id: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
        SELECT d.*, 
               comp.name as company_name,
               (c.first_name || ' ' || c.last_name) as contact_name
        FROM deals d
        LEFT JOIN companies comp ON d.company_id = comp.id
        LEFT JOIN contacts c ON d.contact_id = c.id
        WHERE 1=1
        """
        params = []
        if stage:
            query += " AND d.stage = ?"
            params.append(stage)
        if company_id:
            query += " AND d.company_id = ?"
            params.append(company_id)
        if search:
            query += " AND d.title LIKE ?"
            params.append(f"%{search}%")
        query += " ORDER BY d.id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

@router.post("", response_model=DealResponse, status_code=201)
def create_deal(deal: DealCreate, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO deals (title, company_id, contact_id, amount, stage, probability, expected_close_date, assigned_user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (deal.title, deal.company_id, deal.contact_id, deal.amount, deal.stage, deal.probability, deal.expected_close_date, current_user["id"]))
        deal_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                       (current_user["id"], "DEAL_CREATED", "deal", deal_id, f"Created deal '{deal.title}' for ${deal.amount:,.2f} in stage {deal.stage}"))
        
        cursor.execute("""
        SELECT d.*, 
               comp.name as company_name,
               (c.first_name || ' ' || c.last_name) as contact_name
        FROM deals d
        LEFT JOIN companies comp ON d.company_id = comp.id
        LEFT JOIN contacts c ON d.contact_id = c.id
        WHERE d.id = ?
        """, (deal_id,))
        return dict(cursor.fetchone())

@router.get("/{deal_id}", response_model=DealResponse)
def get_deal(deal_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT d.*, 
               comp.name as company_name,
               (c.first_name || ' ' || c.last_name) as contact_name
        FROM deals d
        LEFT JOIN companies comp ON d.company_id = comp.id
        LEFT JOIN contacts c ON d.contact_id = c.id
        WHERE d.id = ?
        """, (deal_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Deal not found")
        return dict(row)

@router.put("/{deal_id}", response_model=DealResponse)
def update_deal(deal_id: int, deal: DealCreate, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, stage, amount FROM deals WHERE id = ?", (deal_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Deal not found")
        
        cursor.execute("""
        UPDATE deals SET title=?, company_id=?, contact_id=?, amount=?, stage=?, probability=?, expected_close_date=?
        WHERE id=?
        """, (deal.title, deal.company_id, deal.contact_id, deal.amount, deal.stage, deal.probability, deal.expected_close_date, deal_id))
        
        if existing["stage"] != deal.stage:
            action_name = "DEAL_WON" if deal.stage == "closed_won" else ("DEAL_LOST" if deal.stage == "closed_lost" else "STAGE_CHANGE")
            cursor.execute("INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                           (current_user["id"], action_name, "deal", deal_id, f"Deal shifted from {existing['stage']} to {deal.stage}"))
        
        cursor.execute("""
        SELECT d.*, 
               comp.name as company_name,
               (c.first_name || ' ' || c.last_name) as contact_name
        FROM deals d
        LEFT JOIN companies comp ON d.company_id = comp.id
        LEFT JOIN contacts c ON d.contact_id = c.id
        WHERE d.id = ?
        """, (deal_id,))
        return dict(cursor.fetchone())

@router.delete("/{deal_id}", status_code=204)
def delete_deal(deal_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM deals WHERE id = ?", (deal_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Deal not found")
        return None
