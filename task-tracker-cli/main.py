from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from storage import load_tasks, save_tasks

app = FastAPI()
tasks = load_tasks()


class Task(BaseModel):
    id: int
    title: str
    status: str


class NewTask(BaseModel):
    title: str


@app.get("/")
def read_root():
    return {"message": "Welcome to the Task Tracker API"}


@app.get("/tasks/", response_model=List[Task])
def get_tasks():
    return tasks


@app.post("/tasks", response_model=Task)
def add_task(task: NewTask):
    task_id = len(tasks) + 1
    task = {"id": task_id, "title": task.title, "status": "Pending"}
    tasks.append(task)
    save_tasks(tasks)
    return task


@app.put("/tasks/{task_id}/complete", response_model=Task)
def mark_completed(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = "Completed"
            save_tasks(tasks)
            return task
    raise HTTPException(status_code=404, detail="Task not found")


@app.put("/tasks/{task_id}/update", response_model=Task)
def update_task(task_id: int, title: str):
    for task in tasks:
        if task["id"] == task_id:
            task["title"] = title
            save_tasks(tasks)
            return task
    raise HTTPException(status_code=404, detail="Task not found")


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            tasks.remove(task)
            save_tasks(tasks)
            return {"message": "Task deleted"}
    raise HTTPException(status_code=404, detail="Task not found")
