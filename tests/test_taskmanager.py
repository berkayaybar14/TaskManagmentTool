import pytest
from src.taskmanager import TaskManager

@pytest.fixture
def task_manager():
    # In-memory SQLite database for testing
    manager = TaskManager(':memory:')
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
    
# Test deleting a task
def test_delete_task(task_manager, sample_task_data):
    task_id = task_manager.add_task(
        sample_task_data['title'],
        sample_task_data['description'],
        sample_task_data['due_date']
    )
    # Delete the added task
    result = task_manager.delete_task(task_id)
    assert result == True
    assert task_manager.get_task(task_id) is None
    
# Test updating the status of a task
def test_update_task_status(task_manager, sample_task_data):
    task_id = task_manager.add_task(
        sample_task_data['title'],
        sample_task_data['description'],
        sample_task_data['due_date']
    )
    task_manager.update_task_status(task_id, 'completed')
    task = task_manager.get_task(task_id)
    assert task[3] == 'completed'
    
# Test getting all tasks
def test_get_all_task(task_manager):
    task_data = [
        ('Task 1', 'Description 1', '2024-10-01'),
        ('Task 2', 'Description 2', '2024-10-02'),
        ('Task 3', 'Description 3', '2024-10-03')
    ]
    
    for t, d, dd in task_data:
        task_manager.add_task(t, d, dd)
    
    tasks = task_manager.get_all_tasks()
    assert len(tasks) == 3
    assert tasks[0][1] == 'Task 1'
    assert tasks[1][1] == 'Task 2'
    assert tasks[2][1] == 'Task 3'
    
# Test checking if task exists
def test_task_exists(task_manager, sample_task_data):
    task_id = task_manager.add_task(
        sample_task_data['title'],
        sample_task_data['description'],
        sample_task_data['due_date']
    )
    assert task_manager.task_exists(task_id) is True
    assert task_manager.task_exists(99) is False

@pytest.mark.parametrize("invalid_id", [
    -1,     # negative ID
    0,      # zero ID
    999,    # non-existent ID
])

# Test handling of invalid IDs
def test_invalid_task_id(task_manager, invalid_id):
    assert task_manager.task_exists(invalid_id) is False
    assert task_manager.get_task(invalid_id) is None
    assert task_manager.delete_task(invalid_id) is False
