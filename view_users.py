import sqlite3
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def view_all_users():
    database_url = os.getenv("DATABASE_URL")
    db_path = "decision_broker.db"
    
    if database_url:
        print(f"🔗 Connecting to Production Database (PostgreSQL)...")
        try:
            conn = psycopg2.connect(database_url, sslmode='require')
            cursor = conn.cursor(cursor_factory=RealDictCursor)
        except Exception as e:
            print(f"❌ PostgreSQL Connection Error: {e}")
            return
    else:
        print(f"📁 Connecting to Local Database (SQLite)...")
        if not os.path.exists(db_path):
            print("\n❌ SQLite Database not found locally.")
            return
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

    try:
        # Check available columns
        if database_url:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'")
            cols_in_db = [row['column_name'] for row in cursor.fetchall()]
        else:
            cursor.execute("PRAGMA table_info(users)")
            cols_in_db = [column[1] for column in cursor.fetchall()]
        
        # Build query
        possible_cols = ["id", "credits", "email", "subscription_plan", "created_at", "api_key"]
        to_select = [c for c in possible_cols if c in cols_in_db]
        
        if not to_select:
            print("Error: users table found but no recognizable columns exist!")
            return

        query = f"SELECT {', '.join(to_select)} FROM users"
        if "created_at" in cols_in_db:
            query += " ORDER BY created_at DESC"
            
        cursor.execute(query)
        users = cursor.fetchall()

        if not users:
            print("\nℹ️  Database is empty. No users found.")
            return

        print("\n=== 👥 DECISION BROKER: REGISTERED USERS ===")
        # Header Dynamic
        header_parts = []
        if 'email' in cols_in_db: header_parts.append(f"{'Email':<30}")
        if 'credits' in cols_in_db: header_parts.append(f"{'Credits':<8}")
        if 'subscription_plan' in cols_in_db: header_parts.append(f"{'Plan':<10}")
        if 'created_at' in cols_in_db: header_parts.append("Joined At")
        
        header_str = " | ".join(header_parts)
        print(header_str)
        print("-" * len(header_str))

        for user in users:
            row_parts = []
            if 'email' in cols_in_db: 
                val = user['email'] if user['email'] else "Not Set"
                row_parts.append(f"{val:<30}")
            if 'credits' in cols_in_db: 
                row_parts.append(f"{str(user['credits']):<8}")
            if 'subscription_plan' in cols_in_db: 
                val = user['subscription_plan'] if user['subscription_plan'] else "Starter"
                row_parts.append(f"{val:<10}")
            if 'created_at' in cols_in_db:
                row_parts.append(str(user['created_at']))
            
            print(" | ".join(row_parts))
        
        print(f"\nTotal Users: {len(users)}\n")

    except Exception as e:
        print(f"Error reading database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    view_all_users()
