from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from app.database import get_db
from app.schemas import TaskCreate, TaskResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

@router.get("", response_model=List[TaskResponse])
def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        query += " ORDER BY CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END, id DESC"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

@router.post("", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO tasks (title, description, due_date, priority, status, related_entity_type, related_entity_id, assigned_user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (task.title, task.description, task.due_date, task.priority, task.status, task.related_entity_type, task.related_entity_id, current_user["id"]))
        task_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                       (current_user["id"], "TASK_CREATED", "task", task_id, f"Created task '{task.title}' with priority {task.priority}"))
        
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return dict(cursor.fetchone())

@router.patch("/{task_id}/status", response_model=TaskResponse)
def update_task_status(task_id: int, status: str, current_user: dict = Depends(get_current_user)):
    valid_statuses = ['pending', 'in_progress', 'completed']
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of {valid_statuses}")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        
        cursor.execute("INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
                       (current_user["id"], "TASK_STATUS_UPDATED", "task", task_id, f"Marked task {task_id} as {status}"))
        
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return dict(cursor.fetchone())

@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        return None
