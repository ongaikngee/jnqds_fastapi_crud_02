from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="TODO CRUD API", version="1.0.0")

# ============== Models ==============
class TodoBase(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False

class TodoCreate(TodoBase):
    pass

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

class Todo(TodoBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============== In-memory database ==============
todos_db: dict[int, dict] = {}
next_id: int = 1

# ============== Helper functions ==============
def get_next_id() -> int:
    global next_id
    current_id = next_id
    next_id += 1
    return current_id

# ============== Root endpoint ==============
@app.get("/")
def root():
    return {
        "message": "TODO CRUD API",
        "endpoints": {
            "create": "POST /todos",
            "read_all": "GET /todos",
            "read_one": "GET /todos/{id}",
            "update": "PUT /todos/{id}",
            "delete": "DELETE /todos/{id}"
        }
    }

# ============== CREATE ==============
@app.post("/todos", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(todo: TodoCreate):
    """Create a new TODO"""
    todo_id = get_next_id()
    todo_data = {
        "id": todo_id,
        "title": todo.title,
        "description": todo.description,
        "completed": todo.completed,
        "created_at": datetime.now()
    }
    todos_db[todo_id] = todo_data
    return todo_data

# ============== READ ==============
@app.get("/todos", response_model=List[Todo])
def read_todos(skip: int = 0, limit: int = 10, completed: Optional[bool] = None):
    """Get all TODOs with optional filtering"""
    todos_list = list(todos_db.values())
    
    # Filter by completed status if specified
    if completed is not None:
        todos_list = [todo for todo in todos_list if todo["completed"] == completed]
    
    # Apply pagination
    return todos_list[skip:skip + limit]

@app.get("/todos/{todo_id}", response_model=Todo)
def read_todo(todo_id: int):
    """Get a specific TODO by ID"""
    if todo_id not in todos_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"TODO with id {todo_id} not found"
        )
    return todos_db[todo_id]

# ============== UPDATE ==============
@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, todo_update: TodoUpdate):
    """Update a specific TODO"""
    if todo_id not in todos_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"TODO with id {todo_id} not found"
        )
    
    existing_todo = todos_db[todo_id]
    
    # Update only provided fields
    if todo_update.title is not None:
        existing_todo["title"] = todo_update.title
    if todo_update.description is not None:
        existing_todo["description"] = todo_update.description
    if todo_update.completed is not None:
        existing_todo["completed"] = todo_update.completed
    
    return existing_todo

# ============== DELETE ==============
@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int):
    """Delete a specific TODO"""
    if todo_id not in todos_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"TODO with id {todo_id} not found"
        )
    
    del todos_db[todo_id]
    return None

# ============== Utility endpoints ==============
@app.get("/todos/stats/summary")
def get_stats():
    """Get TODO statistics"""
    total = len(todos_db)
    completed = sum(1 for todo in todos_db.values() if todo["completed"])
    pending = total - completed
    
    return {
        "total_todos": total,
        "completed": completed,
        "pending": pending,
        "completion_percentage": (completed / total * 100) if total > 0 else 0
    }

@app.delete("/todos", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_todos():
    """Delete all TODOs"""
    global todos_db
    todos_db.clear()
    return None