from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from app.database import get_db
from app.schemas import CompanyCreate, CompanyResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/companies", tags=["Companies"])

@router.get("", response_model=List[CompanyResponse])
def list_companies(
    search: Optional[str] = Query(None, description="Search by name or industry"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM companies WHERE 1=1"
        params = []
        if search:
            query += " AND (name LIKE ? OR industry LIKE ? OR city LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term])
        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

@router.post("", response_model=CompanyResponse, status_code=201)
def create_company(company: CompanyCreate, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO companies (name, industry, website, size, annual_revenue, city, country)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (company.name, company.industry, company.website, company.size, company.annual_revenue, company.city, company.country))
        company_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                       (current_user["id"], "COMPANY_CREATED", "company", company_id, f"Created company {company.name}"))
        
        cursor.execute("SELECT * FROM companies WHERE id = ?", (company_id,))
        row = cursor.fetchone()
        return dict(row)

@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM companies WHERE id = ?", (company_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Company not found")
        return dict(row)

@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(company_id: int, company: CompanyCreate, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM companies WHERE id = ?", (company_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Company not found")
        
        cursor.execute("""
        UPDATE companies SET name=?, industry=?, website=?, size=?, annual_revenue=?, city=?, country=?
        WHERE id=?
        """, (company.name, company.industry, company.website, company.size, company.annual_revenue, company.city, company.country, company_id))
        
        cursor.execute("SELECT * FROM companies WHERE id = ?", (company_id,))
        return dict(cursor.fetchone())

@router.delete("/{company_id}", status_code=204)
def delete_company(company_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM companies WHERE id = ?", (company_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Company not found")
        return None
