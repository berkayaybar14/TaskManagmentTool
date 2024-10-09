import sqlite3

class TaskManager:
    # Initialize the sqlite connection and create the table
    def __init__(self, db_path='tasks.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
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
