import os
import time
import timeago
import pymysql

from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_HOST = os.getenv("RSVP_DATABASE_HOST")
DATABASE_USER = os.getenv("RSVP_DATABASE_USER")
DATABASE_PASSWORD = os.getenv("RSVP_DATABASE_PASSWORD")
DATABASE_NAME = os.getenv("RSVP_DATABASE_NAME")

def create_connection():
    max_retries = 5
    retry_delay = 5  # seconds

    for attempt in range(max_retries):
        try:
            return pymysql.connect(
                host=DATABASE_HOST,
                user=DATABASE_USER,
                password=DATABASE_PASSWORD,
                database=DATABASE_NAME,
                cursorclass=pymysql.cursors.DictCursor
            )
        except pymysql.Error as e:
            if attempt == max_retries - 1:
                raise e
            print(f"Database connection attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

def init_db():
    conn = create_connection()
    cursor = conn.cursor()
    # Original RSVP table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rsvp (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(255) NOT NULL,
            message TEXT NULL,
            attendance VARCHAR(50) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # New Comments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            rsvp_id INTEGER NOT NULL,
            name VARCHAR(255) NOT NULL,
            comment TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (rsvp_id) REFERENCES rsvp (id)
        )
    ''')

    # New Persons table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            code VARCHAR(50) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            gender VARCHAR(10) NOT NULL CHECK(gender IN ('male', 'female')),
            title VARCHAR(100) NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def person_get(code):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT code, name, gender, title FROM persons WHERE LOWER(code) = LOWER(%s)
    ''', (code,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'code': row['code'],
            'name': row['name'],
            'gender': row['gender'],
            'title':  row['title'],
        }
    else:
        return None

def person_list_with_rsvp_status(search=None):
    conn = create_connection()
    cursor = conn.cursor()
    query = '''
        SELECT p.code, p.name, p.gender, p.title,
               CASE WHEN r.name IS NOT NULL THEN 1 ELSE 0 END as has_rsvp
        FROM persons p
        LEFT JOIN (
            SELECT DISTINCT name
            FROM rsvp
            WHERE is_active = 1
            GROUP BY name
        ) r ON UPPER(p.name) = UPPER(r.name)
    '''
    
    params = []
    
    if search:
        query += ' WHERE p.name LIKE %s'
        params.append(f'%{search}%')
    
    query += ' ORDER BY p.name'
    cursor.execute(query, params)
    persons = cursor.fetchall()
    conn.close()
    return [{'code': p['code'], 'name': p['name'], 'gender': p['gender'], 'title': p['title'], 'has_rsvp': p['has_rsvp']} for p in persons]

def person_create(code: str, name: str, gender: str, title: str = None):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO persons (code, name, gender, title)
        VALUES (%s, %s, %s, %s)
    ''', (code, name, gender, title))
    conn.commit()
    result = cursor.lastrowid
    conn.close()
    return result

def person_update(code: str, name: str, gender: str, title: str = None):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE persons SET name = %s, gender = %s, title = %s WHERE LOWER(code) = LOWER(%s)
    ''', (name, gender, title, code))
    conn.commit()
    conn.close()

def person_delete(code: str):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM persons WHERE LOWER(code) = LOWER(%s)
    ''', (code,))
    conn.commit()
    conn.close()

def person_get_total():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM persons")
    total = cursor.fetchone()['COUNT(*)']
    conn.close()
    return total

def rsvp_list(attendance=None, has_last_comment=None):
    conn = create_connection()
    cursor = conn.cursor()
    query = '''
        SELECT r.id, r.name, r.attendance, r.message, 
               (SELECT comment FROM comments c WHERE c.rsvp_id = r.id ORDER BY c.created_at DESC LIMIT 1) as last_comment, 
               r.created_at, r.is_active
        FROM rsvp r
    '''
    params = []
    if attendance:
        query += ' WHERE r.attendance = %s'
        params.append(attendance)
    
    if has_last_comment:
        if attendance:
            query += ' AND'
        else:
            query += ' WHERE'
        if has_last_comment == 'yes':
            query += ' EXISTS (SELECT 1 FROM comments c WHERE c.rsvp_id = r.id)'
        else:
            query += ' NOT EXISTS (SELECT 1 FROM comments c WHERE c.rsvp_id = r.id)'
    
    query += ' ORDER BY r.created_at DESC'
    
    cursor.execute(query, params)
    rsvps = cursor.fetchall()
    conn.close()
    return rsvps

def rsvp_get_total(show_all=False):
    conn = create_connection()
    cursor = conn.cursor()
    if show_all:
        cursor.execute("SELECT COUNT(*) FROM rsvp")
    else:
        cursor.execute("SELECT COUNT(*) FROM rsvp WHERE is_active = 1")
    total = cursor.fetchone()['COUNT(*)']
    conn.close()
    return total

def rsvp_confirm(name: str, message: str, attendance: str):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO rsvp (name, message, attendance) VALUES (%s, %s, %s)
    ''', (name, message, attendance))
    conn.commit()
    result = cursor.lastrowid
    conn.close()
    return result

def comment_create(rsvp_id: int, name: str, comment: str):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO comments (rsvp_id, name, comment) 
        VALUES (%s, %s, %s)
    ''', (rsvp_id, name, comment))
    conn.commit()
    result = cursor.lastrowid
    conn.close()
    return result

def rsvp_toogle_status(rsvp_id: int):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE rsvp SET is_active = NOT is_active WHERE id = %s
    ''', (rsvp_id,))
    conn.commit()
    result = cursor.rowcount > 0
    conn.close()
    return result

def rsvp_list_with_comments():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            r.id,
            r.name,
            r.message,
            r.attendance,
            r.created_at,
            c.id as comment_id,
            c.name as commenter_name,
            c.comment,
            c.created_at as comment_created_at
        FROM rsvp r
        LEFT JOIN comments c ON r.id = c.rsvp_id
        WHERE r.is_active = 1
        ORDER BY r.created_at DESC, c.created_at ASC
    ''')

    results = cursor.fetchall()
    
    now = datetime.utcnow()
    rsvps = {}
    for row in results:
        rsvp_id = row['id']
        if rsvp_id not in rsvps:
            rsvps[rsvp_id] = {
                'id': rsvp_id,
                'name': row['name'],
                'message': row['message'],
                'attendance': row['attendance'],
                'created_at': row['created_at'],
                'timeago': timeago.format(row['created_at'], now, 'in_ID'),
                'comments': []
            }
        
        if row['comment_id']:
            comment = {
                'id': row['comment_id'],
                'name': row['commenter_name'],
                'comment': row['comment'],
                'created_at': row['comment_created_at'],
                'timeago': timeago.format(row['comment_created_at'], now, 'in_ID'),
            }
            rsvps[rsvp_id]['comments'].append(comment)
    
    conn.close()
    return list(rsvps.values())

def rsvp_get_with_comments(rsvp_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, message, attendance, created_at, is_active
        FROM rsvp WHERE id = %s
    ''', (rsvp_id,))
    rsvp = cursor.fetchone()

    if rsvp:
        cursor.execute('''
            SELECT id, name, comment, created_at
            FROM comments 
            WHERE rsvp_id = %s 
            ORDER BY created_at DESC
        ''', (rsvp_id,))
        comments = cursor.fetchall()

        rsvp_dict = dict(rsvp)
        rsvp_dict['comments'] = [dict(comment) for comment in comments]

        conn.close()
        return rsvp_dict
    else:
        conn.close()
        return None

