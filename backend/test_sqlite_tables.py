import sqlite3

def run():
    try:
        conn = sqlite3.connect('arenamind.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        with open('test_out.txt', 'w') as f:
            f.write(f"Tables found: {tables}\n")
            
            # If decisions table exists, inspect its schema
            if ('decisions',) in tables:
                cursor.execute("PRAGMA table_info(decisions)")
                f.write(f"Decisions columns: {cursor.fetchall()}\n")
            else:
                f.write("Decisions table NOT found!\n")
                
    except Exception as e:
        with open('test_out.txt', 'w') as f:
            f.write(f"Error: {e}\n")

if __name__ == "__main__":
    run()
