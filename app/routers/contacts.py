from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from app.database import get_db
from app.schemas import ContactCreate, ContactResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/contacts", tags=["Contacts"])

@router.get("", response_model=List[ContactResponse])
def list_contacts(
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
        SELECT c.*, comp.name as company_name 
        FROM contacts c
        LEFT JOIN companies comp ON c.company_id = comp.id
        WHERE 1=1
        """
        params = []
        if status:
            query += " AND c.status = ?"
            params.append(status)
        if search:
            query += " AND (c.first_name LIKE ? OR c.last_name LIKE ? OR c.email LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term])
        query += " ORDER BY c.id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

@router.post("", response_model=ContactResponse, status_code=201)
def create_contact(contact: ContactCreate, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM contacts WHERE email = ?", (contact.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Contact with this email already exists")
        
        cursor.execute("""
        INSERT INTO contacts (company_id, first_name, last_name, email, phone, title, status, lead_source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (contact.company_id, contact.first_name, contact.last_name, contact.email, contact.phone, contact.title, contact.status, contact.lead_source))
        contact_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                       (current_user["id"], "CONTACT_CREATED", "contact", contact_id, f"Created contact {contact.first_name} {contact.last_name}"))
        
        cursor.execute("""
        SELECT c.*, comp.name as company_name 
        FROM contacts c
        LEFT JOIN companies comp ON c.company_id = comp.id
        WHERE c.id = ?
        """, (contact_id,))
        return dict(cursor.fetchone())

@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(contact_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT c.*, comp.name as company_name 
        FROM contacts c
        LEFT JOIN companies comp ON c.company_id = comp.id
        WHERE c.id = ?
        """, (contact_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Contact not found")
        return dict(row)

@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: int, contact: ContactCreate, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM contacts WHERE id = ?", (contact_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Contact not found")
        
        cursor.execute("""
        UPDATE contacts SET company_id=?, first_name=?, last_name=?, email=?, phone=?, title=?, status=?, lead_source=?
        WHERE id=?
        """, (contact.company_id, contact.first_name, contact.last_name, contact.email, contact.phone, contact.title, contact.status, contact.lead_source, contact_id))
        
        cursor.execute("""
        SELECT c.*, comp.name as company_name 
        FROM contacts c
        LEFT JOIN companies comp ON c.company_id = comp.id
        WHERE c.id = ?
        """, (contact_id,))
        return dict(cursor.fetchone())

@router.delete("/{contact_id}", status_code=204)
def delete_contact(contact_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Contact not found")
        return None
