import pytest
import sqlite3
from src.taskmanager import TaskManger

@pytest.fixture
def task_manager():
    # In-memory SQLite database for testing
    manager = TaskManger(':memory:')
    yield manager
    manager.close()

@pytest.fixture
def sample_task_data():
    return {
        'title': 'Test Task',
        'description': 'This is a test task',
        'due_date': '2024-12-31'
    }
    
# Test creating a new task
def test_create_task(task_manager, sample_task_data):
    task_id = task_manager.add_task(
        sample_task_data['title'],
        sample_task_data['description'],
        sample_task_data['due_date']
    ) 
    
    assert task_id == 1
    task = task_manager.get_task(task_id)
    assert task is not None
    assert task[1] == sample_task_data['title']
    assert task[2] == sample_task_data['description']
