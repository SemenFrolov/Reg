import os
import psycopg2
import zmq
from hashlib import sha256
import time

def init_db():
    max_retries = 10 #Тут сервер ранился раньше, чем порт гес и были ошибки, вот так пофиксил
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port="5432"
            )
            
            # Создаем таблицу, если ее нет
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        password_hash VARCHAR(64) NOT NULL
                    )
                """)
                conn.commit()
            
            print("Successfully connected to PostgreSQL")
            return conn
            
        except psycopg2.OperationalError as e:
            print(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(retry_delay)

def register_user(conn, username, password):
    password_hash = sha256(password.encode()).hexdigest()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, password_hash)
            )
            conn.commit()
            return True
    except psycopg2.IntegrityError:
        return False

def login_user(conn, username, password):
    password_hash = sha256(password.encode()).hexdigest()
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM users WHERE username = %s AND password_hash = %s",
            (username, password_hash)
        )
        return cursor.fetchone() is not None

def main():
    conn = init_db()
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")  # Так на сервере пишем (BIND)

    print("Сервер запущен и ждёт сообщений...")

    while True:
        try:
            message = socket.recv_string()
            print(f"Получено сообщение: {message}")
            
            try:
                command, username, password = message.split(":", 2)
            except ValueError:
                socket.send_string("Invalid message format. Use: command:username:password")
                continue
                
            try:
                if command == "register":
                    success = register_user(conn, username, password)
                    response = "Registration successful" if success else "Username already exists"
                elif command == "login":
                    success = login_user(conn, username, password)
                    response = "Login successful" if success else "Invalid credentials"
                else:
                    response = "Unknown command"
                    
                socket.send_string(response)
                
            except psycopg2.Error as e:
                print(f"Database error: {e}")
                socket.send_string("Database error occurred")
                
        except Exception as e:
            print(f"Server error: {e}")
            # Пересоздаем соединение с БД при критических ошибках
            try:
                conn.close()
            except:
                pass
            conn = init_db()

if __name__ == "__main__":
    main()