from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from app.database import get_db
from app.schemas import LeadCreate, LeadResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/leads", tags=["Leads"])

@router.get("", response_model=List[LeadResponse])
def list_leads(
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
        SELECT l.*, 
               (c.first_name || ' ' || c.last_name) as contact_name,
               comp.name as company_name
        FROM leads l
        LEFT JOIN contacts c ON l.contact_id = c.id
        LEFT JOIN companies comp ON l.company_id = comp.id
        WHERE 1=1
        """
        params = []
        if status:
            query += " AND l.status = ?"
            params.append(status)
        if search:
            query += " AND (l.title LIKE ? OR l.source LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term])
        query += " ORDER BY l.id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

@router.post("", response_model=LeadResponse, status_code=201)
def create_lead(lead: LeadCreate, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO leads (title, contact_id, company_id, value, status, source, notes, assigned_user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (lead.title, lead.contact_id, lead.company_id, lead.value, lead.status, lead.source, lead.notes, current_user["id"]))
        lead_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                       (current_user["id"], "LEAD_CREATED", "lead", lead_id, f"Created lead {lead.title} (${lead.value})"))
        
        cursor.execute("""
        SELECT l.*, 
               (c.first_name || ' ' || c.last_name) as contact_name,
               comp.name as company_name
        FROM leads l
        LEFT JOIN contacts c ON l.contact_id = c.id
        LEFT JOIN companies comp ON l.company_id = comp.id
        WHERE l.id = ?
        """, (lead_id,))
        return dict(cursor.fetchone())

@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT l.*, 
               (c.first_name || ' ' || c.last_name) as contact_name,
               comp.name as company_name
        FROM leads l
        LEFT JOIN contacts c ON l.contact_id = c.id
        LEFT JOIN companies comp ON l.company_id = comp.id
        WHERE l.id = ?
        """, (lead_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Lead not found")
        return dict(row)

@router.put("/{lead_id}", response_model=LeadResponse)
def update_lead(lead_id: int, lead: LeadCreate, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, status FROM leads WHERE id = ?", (lead_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        cursor.execute("""
        UPDATE leads SET title=?, contact_id=?, company_id=?, value=?, status=?, source=?, notes=?
        WHERE id=?
        """, (lead.title, lead.contact_id, lead.company_id, lead.value, lead.status, lead.source, lead.notes, lead_id))
        
        if existing["status"] != lead.status:
            cursor.execute("INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                           (current_user["id"], "LEAD_STATUS_CHANGED", "lead", lead_id, f"Lead status updated to {lead.status}"))
        
        cursor.execute("""
        SELECT l.*, 
               (c.first_name || ' ' || c.last_name) as contact_name,
               comp.name as company_name
        FROM leads l
        LEFT JOIN contacts c ON l.contact_id = c.id
        LEFT JOIN companies comp ON l.company_id = comp.id
        WHERE l.id = ?
        """, (lead_id,))
        return dict(cursor.fetchone())

@router.delete("/{lead_id}", status_code=204)
def delete_lead(lead_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Lead not found")
        return None
