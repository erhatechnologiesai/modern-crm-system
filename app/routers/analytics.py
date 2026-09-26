from fastapi import APIRouter, Depends
from app.database import get_db
from app.schemas import DashboardMetrics, ActivityLogResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["Analytics & Dashboard"])

@router.get("/dashboard", response_model=DashboardMetrics)
def get_dashboard_summary(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Total revenue won
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM deals WHERE stage = 'closed_won'")
        total_revenue_won = cursor.fetchone()[0]
        
        # Pipeline total value
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM deals WHERE stage NOT IN ('closed_lost')")
        pipeline_total_value = cursor.fetchone()[0]
        
        # Total counts
        cursor.execute("SELECT COUNT(*) FROM contacts")
        total_contacts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM companies")
        total_companies = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM deals")
        total_deals = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM leads")
        total_leads = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status != 'completed'")
        active_tasks = cursor.fetchone()[0]
        
        # Deals count and value grouped by stage
        cursor.execute("""
        SELECT stage, COUNT(*) as count, COALESCE(SUM(amount), 0) as total_val
        FROM deals
        GROUP BY stage
        """)
        deals_by_stage = {row["stage"]: {"count": row["count"], "value": row["total_val"]} for row in cursor.fetchall()}
        
        # Recent activity logs
        cursor.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT 10")
        recent_activities = [dict(row) for row in cursor.fetchall()]
        
        return DashboardMetrics(
            total_revenue_won=total_revenue_won,
            pipeline_total_value=pipeline_total_value,
            total_contacts=total_contacts,
            total_companies=total_companies,
            total_deals=total_deals,
            total_leads=total_leads,
            active_tasks=active_tasks,
            deals_by_stage=deals_by_stage,
            recent_activities=recent_activities
        )
