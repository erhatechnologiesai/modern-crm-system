import os
import pytest
from starlette.testclient import TestClient
from app.main import app
from app.database import init_db

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    os.environ["DATABASE_PATH"] = "test_crm.db"
    init_db()
    yield
    if os.path.exists("test_crm.db"):
        try:
            os.remove("test_crm.db")
        except Exception:
            pass

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ApexCRM"

def test_login_success():
    response = client.post("/api/auth/login", json={
        "email": "admin@apexcrm.io",
        "password": "Admin@Apex2026!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "admin"
    assert data["user"]["email"] == "admin@apexcrm.io"

def test_login_invalid_password():
    response = client.post("/api/auth/login", json={
        "email": "admin@apexcrm.io",
        "password": "WrongPassword!"
    })
    assert response.status_code == 401

def test_register_new_user():
    response = client.post("/api/auth/register", json={
        "email": "newuser@apexcrm.io",
        "full_name": "Test User",
        "password": "TestPassword123!",
        "role": "sales_rep"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@apexcrm.io"
    assert data["role"] == "sales_rep"

def get_auth_token():
    res = client.post("/api/auth/login", json={
        "email": "admin@apexcrm.io",
        "password": "Admin@Apex2026!"
    })
    return res.json()["access_token"]

def test_companies_crud():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create Company
    create_res = client.post("/api/companies", headers=headers, json={
        "name": "Nova Dynamics",
        "industry": "Aerospace",
        "website": "https://novadynamics.io",
        "size": "500-1000",
        "annual_revenue": 75000000.0,
        "city": "Seattle",
        "country": "USA"
    })
    assert create_res.status_code == 201
    comp = create_res.json()
    assert comp["name"] == "Nova Dynamics"
    comp_id = comp["id"]

    # List Companies
    list_res = client.get("/api/companies", headers=headers)
    assert list_res.status_code == 200
    assert any(c["id"] == comp_id for c in list_res.json())

    # Get Single Company
    get_res = client.get(f"/api/companies/{comp_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Nova Dynamics"

    # Update Company
    update_res = client.put(f"/api/companies/{comp_id}", headers=headers, json={
        "name": "Nova Dynamics Global",
        "industry": "Aerospace & Defense",
        "annual_revenue": 85000000.0
    })
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Nova Dynamics Global"

def test_contacts_crud():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create Contact
    create_res = client.post("/api/contacts", headers=headers, json={
        "first_name": "Alexander",
        "last_name": "Pierce",
        "email": "a.pierce@shield.gov",
        "phone": "+1-202-555-0199",
        "title": "Director",
        "status": "lead",
        "lead_source": "Government RFP"
    })
    assert create_res.status_code == 201
    contact = create_res.json()
    contact_id = contact["id"]

    # Search Contact
    search_res = client.get("/api/contacts?search=Alexander", headers=headers)
    assert search_res.status_code == 200
    assert len(search_res.json()) >= 1
    assert search_res.json()[0]["email"] == "a.pierce@shield.gov"

def test_deals_pipeline():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create Deal
    create_res = client.post("/api/deals", headers=headers, json={
        "title": "Enterprise Security Gateway Renewal",
        "amount": 125000.0,
        "stage": "proposal",
        "probability": 70,
        "expected_close_date": "2026-11-30"
    })
    assert create_res.status_code == 201
    deal = create_res.json()
    assert deal["amount"] == 125000.0
    deal_id = deal["id"]

    # Update Stage to closed_won
    update_res = client.put(f"/api/deals/{deal_id}", headers=headers, json={
        "title": "Enterprise Security Gateway Renewal",
        "amount": 125000.0,
        "stage": "closed_won",
        "probability": 100
    })
    assert update_res.status_code == 200
    assert update_res.json()["stage"] == "closed_won"

def test_tasks_lifecycle():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create Task
    task_res = client.post("/api/tasks", headers=headers, json={
        "title": "Deliver Q4 Executive Review",
        "description": "Compile slide deck for stakeholder meeting",
        "due_date": "2026-10-15",
        "priority": "urgent",
        "status": "pending"
    })
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    # Update Status
    patch_res = client.patch(f"/api/tasks/{task_id}/status?status=completed", headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "completed"

def test_analytics_dashboard():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    dash_res = client.get("/api/analytics/dashboard", headers=headers)
    assert dash_res.status_code == 200
    data = dash_res.json()
    assert "total_revenue_won" in data
    assert "pipeline_total_value" in data
    assert "total_deals" in data
    assert "deals_by_stage" in data
    assert "recent_activities" in data
    assert data["total_revenue_won"] > 0
