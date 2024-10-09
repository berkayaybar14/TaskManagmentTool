import sqlite3
from typing import List

class TaskManager:
    # Initialize the sqlite connection and create the table
    def __init__(self, db_path='tasks.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
    
    # Creates a new table
    def create_tables(self):
        cursor = self.conn.cursor()
        # Create tasks table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date DATE
            ) 
        ''')
        # Create tags table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
            )
        ''')
        # Create junction table for task-tag relationships
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_tags (
            task_id INTEGER,
            tag_id INTEGER,
            PRIMARY KEY (task_id, tag_id),
            FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
            )
        ''')
        self.conn.commit()

    # Adds a new task to the table 
    def add_task(self, title, description, due_date=None, tags=None):
        cursor = self.conn.cursor()
        try:
            self.conn.execute('BEGIN TRANSACTION')
            cursor.execute('''
                INSERT INTO tasks (title, description, due_date)
                VALUES (?, ?, ?) 
            ''', (title, description, due_date))
            task_id = cursor.lastrowid
            
            # Add tags if provided
            if tags:
                self.add_tags_to_task(task_id, tags)

            self.conn.commit()
            return task_id
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"An error occurred: {e}")
            raise
        
    # Returns the tags of a task
    def get_task_tags(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT t.*, GROUP_CONCAT(tags.name) as tags
            FROM tasks t
            LEFT JOIN task_tags tt ON t.id = tt.task_id
            LEFT JOIN tags ON tt.tag_id = tags.id
            WHERE t.id = ?
            GROUP BY t.id
        ''', (task_id,))
        row = cursor.fetchone()
        
        if row:
            task = {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'status': row[3],
                'created_at': row[4],
                'due_date': row[5],
                'tags': row[6].split(',') if row[6] else []
            }
            return task
        return None
    
    # Search tasks by tag
    def search_tasks_by_tag(self, tag: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT t.*, GROUP_CONCAT(tags.name) as tags
            FROM tasks t
            JOIN task_tags tt ON t.id = tt.task_id
            JOIN tags ON tt.tag_id
            WHERE tags.name = ?
            GROUP BY t.id
        ''', (tag.lower(),))
        
        tasks = []
        for row in cursor.fetchall():
            task = {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'status': row[3],
                'created_at': row[4],
                'due_date': row[5],
                'tags': row[6].split(',') if row[6] else []
            }
            tasks.append(task)
        return tasks
        
    # Adds tags to a task
    def add_tags_to_task(self, task_id, tags: List[str]):
        if not self.task_exists(task_id):
            return False
        try:
            cursor = self.conn.cursor()        
            # Insert tags if it doesn't exist yet
            for tag in tags:
                cursor.execute('''
                    INSERT OR IGNORE INTO tags (name)
                    VALUES (?)
                ''', (tag.lower(),))
            # Get tag id
            cursor.execute('SELECT id FROM tags WHERE name = ?', (tag.lower(),))
            tag_id = cursor.fetchone()[0]
            # Link tag to task
            cursor.execute('''
                INSERT OR IGNORE INTO task_tags (task_id, tag_id)
                VALUES (?, ?)
            ''', (task_id, tag_id))
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            return False
        
    # Remove tag from a task
    def remove_tag_from_task(self, task_id, tag: str):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                DELETE FROM task_tags
                WHERE task_id = ? AND tag_id IN (
                SELECT id FROM tags WHERE name = ?
                )
            ''', (task_id, tag.lower()))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            return False
        
    # Returns all tags
    def get_all_tags(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT name FROM tags ORDER BY name')
        return [row[0] for row in cursor.fetchall()]

    # Get a task by id
    def get_task(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        return cursor.fetchone()

    # Returns all entries in the table
    def get_all_tasks(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tasks ORDER BY due_date')
        return cursor.fetchall()

    # Updates the status of a task by task_id
    def update_task_status(self, task_id, status):
        if not self.task_exists(task_id):
            return False
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE tasks
            SET status = ?
            WHERE id = ?
        ''', (status, task_id))
        self.conn.commit()
        return True
        
    # Deletes a task by task_id
    def delete_task(self, task_id):
        if not self.task_exists(task_id):
            return False 
        cursor = self.conn.cursor() 
        # Begin Transaction
        self.conn.execute('BEGIN TRANSACTION') 
        try:
            # Delete the specified task
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            # Get all tasks greater than the deleted task
            cursor.execute('SELECT id FROM tasks WHERE id > ? ORDER BY id', (task_id,))
            tasks_to_update = cursor.fetchall()

            # Update all IDs of the following tasks  
            for id in tasks_to_update:
                new_id = id[0] - 1
                cursor.execute('''
                    UPDATE tasks
                    SET id = ?
                    WHERE id = ? 
                ''', (new_id, id[0]))
            
            # Reset autoincrement counter
            cursor.execute('''
                UPDATE sqlite_sequence 
                SET seq = (SELECT MAX(id) FROM tasks)
                WHERE name = 'tasks'
            ''')

            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"An errror occurred: {e}")
            return False
    
    # Check if the task with the given id exists
    def task_exists(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM tasks WHERE id = ?', (task_id,))
        return cursor.fetchone()[0] > 0

    def close(self):
        self.conn.close()
        
def main():
    task_manager = TaskManager()

    while True:
        print("\n=== Task Management System ===")
        print("1. Add Task")
        print("2. Get one Task")
        print("3. View All Tasks")
        print("4. Mark Task as Complete")
        print("5. Delete Task")
        print("6. Exit")
        
        choice = input("\nChoose a option (1-6): ")
        
        if 5 < int(choice) < 1:
            print("Invalid choice. Please try again!")

        match choice:

            case "1":
                title = input("Enter task title: ")
                description = input("Enter your description: ")
                due_date = input("Enter due date (YYYY-MM-DD HH:MM:SS) or press enter to skip: ")
                due_date = due_date if due_date else None
                task_manager.add_task(title, description, due_date)
                print("The task was successfully added!")

            case "2":
                task_id = int(input("Enter task ID to view: ")) 
                task = task_manager.get_task(task_id)
                if task:
                    print(f"\nID: {task[0]}")
                    print(f"Title: {task[1]}")
                    print(f"Description: {task[2]}")
                    print(f"Status: {task[3]}")
                    print(f"Created: {task[4]}")
                    print(f"Due: {task[5] if task[5] else 'No due date'}")
                else:
                    print(f"No task found with ID {task_id}") 

            case "3":
                tasks = task_manager.get_all_tasks()
                if not tasks:
                    print("No tasks found!")
                else:
                    print("\nCurrent Tasks:")
                    for task in tasks:
                        print(f"\nID: {task[0]}")
                        print(f"Title: {task[1]}")
                        print(f"Description: {task[2]}")
                        print(f"Status: {task[3]}")
                        print(f"Created: {task[4]}")
                        print(f"Due: {task[5] if task[5] else 'No due date'}")

            case "4":
                task_id = int(input("Enter task ID to mark as completed: "))
                if task_manager.task_exists(task_id):
                    task_manager.update_task_status(task_id, 'completed')
                    print("Task marked as complete!")
                else:
                    print(f"No task found with ID {task_id}")
                    
            case "5":
                task_id = int(input("Enter task ID to delete: "))
                if task_manager.task_exists(task_id):
                    if task_manager.delete_task(task_id):
                        print("Task was deleted!")
                    else:
                        print("Could not delete the task. Please try again!")
                else:
                    print(f"No task found with ID {task_id}")

            case "6":
                task_manager.close()
                print("Goodbye!")
                break
            
if __name__ == "__main__":
    main()
