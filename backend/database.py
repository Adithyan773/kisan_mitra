import psycopg2
import psycopg2.extras
import json
from backend.config import settings

def get_db_connection():
    try:
        conn = psycopg2.connect(settings.postgres_url)
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error: Could not connect to the database. Details: {e}")
        return None

def initialize_db():
    """Creates all necessary tables if they do not already exist."""
    conn = get_db_connection()
    if conn is None:
        return
        
    with conn.cursor() as cur:
        print("Creating 'users' table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                state VARCHAR(255) NOT NULL,
                district VARCHAR(255) NOT NULL,
                city VARCHAR(255) NOT NULL,
                password TEXT NOT NULL
            );
        """)
        
        print("Creating 'agent_sessions' table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_sessions (
                session_id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                state JSONB,
                summary TEXT,
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        print("Creating 'chat_history' table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES agent_sessions(session_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS agent_memory (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                user_id VARCHAR(255) NOT NULL,
                message JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
        """)
    conn.commit()
    conn.close()
    print("Database initialization check complete.")

def register_user(name, state, district, city, password):
    """Registers a new user. Returns True on success, False if user exists."""
    conn = get_db_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (name, state, district, city, password) VALUES (%s, %s, %s, %s, %s)",
                (name, state, district, city, password)
            )
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        return False 
    finally:
        if conn: conn.close()

def login_user(name, password):
    """Authenticates a user. Returns user details dict on success, None on failure."""
    conn = get_db_connection()
    if conn is None: return None
    user = None
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT * FROM users WHERE name = %s AND password = %s", (name, password))
        user_record = cur.fetchone()
        if user_record:
            user = dict(user_record)
    conn.close()
    return user

# --- Agent Memory and History Functions ---

def get_session(session_id):
    conn = get_db_connection()
    if conn is None: return None
    session_data = None
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT * FROM agent_sessions WHERE session_id = %s", (session_id,))
        record = cur.fetchone()
        if record:
            session_data = dict(record)
    conn.close()
    return session_data

def save_session(session_id, user_id, state):
    conn = get_db_connection()
    if conn is None: return
    state_json = json.dumps(state)
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO agent_sessions (session_id, user_id, state)
            VALUES (%s, %s, %s)
            ON CONFLICT (session_id) DO UPDATE SET
                state = EXCLUDED.state,
                last_updated = CURRENT_TIMESTAMP;
        """, (session_id, user_id, state_json))
    conn.commit()
    conn.close()

def add_chat_message(session_id, role, content):
    conn = get_db_connection()
    if conn is None: return
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chat_history (session_id, role, content) VALUES (%s, %s, %s)",
            (session_id, role, content)
        )
    conn.commit()
    conn.close()

def get_chat_history(session_id, limit=4):
    conn = get_db_connection()
    if conn is None: return []
    messages = []
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT role, content FROM chat_history
            WHERE session_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (session_id, limit))
        records = cur.fetchall()
        messages = [dict(row) for row in reversed(records)]
    conn.close()
    return messages