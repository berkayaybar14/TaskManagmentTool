import sqlite3
from datetime import datetime

class TaskManger:
    # Initialize the sqlite connection and create the table
    def __init__(self):
        self.conn = sqlite3.connect('tasks.db')
        self.create_table()
    
    # Creates a new table
    def create_table(self):
        cursor = self.conn.cursor()
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
        self.conn.commit()

    # Adds a new task to the table 
    def add_task(self, title, description, due_date=None):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (title, description, due_date)
            VALUES (?, ?, ?) 
        ''', (title, description, due_date))
        self.conn.commit()
        return cursor.lastrowid

    # Returns all entries in the table
    def get_all_tasks(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tasks ORDER BY due_date')
        return cursor.fetchall()

    # Updates the status of a task by task_id
    def update_task_status(self, task_id, status):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE tasks
        SET status = ?
        WHERE id = ?
    ''', (status, task_id))
        self.conn.commit()
        
    # Deletes a task by task_id
    def delete_task(self, task_id):
        cursor = self.conn.cursor() 
        # Begin Transaction
        self.conn.execute('BEGIN TRANSACTION') 
        try:
            # Delete the specified task
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            # Get all tasks greater than the delted task
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


    def close(self):
        self.conn.close()
        
def main():
    task_manager = TaskManger()

    while True:
        print("\n=== Task Management System ===")
        print("1. Add Task")
        print("2. View All Tasks")
        print("3. Mark Task as Complete")
        print("4. Delete Task")
        print("5. Exit")
        
        choice = input("\nChoose a option (1-5): ")
        
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
            case "3":
                task_id = input("Enter task ID to mark as completed: ")
                task_manager.update_task_status(task_id, 'completed')
                print("Task marked as complete!")
            case "4":
                task_id = input("Enter task ID to delete: ")
                if task_manager.delete_task(int(task_id)):
                    print("Task was deleted!")
                else:
                    print("Could not delete the task. Please try again!")
            case "5":
                task_manager.close()
                print("Goodbye!")
                break
            
if __name__ == "__main__":
    main()
