from flask import Flask, jsonify, request
import os
import pika
import json
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import threading

app = Flask(__name__)

# RabbitMQ Connection
credentials = pika.PlainCredentials(
    os.getenv("RABBITMQ_DEFAULT_USER", "guest"),
    os.getenv("RABBITMQ_DEFAULT_PASS", "guest")
)

retry_attempts = 10
retry_delay = 5

for attempt in range(retry_attempts):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="rabbitmq", credentials=credentials, heartbeat=120)
        )
        channel = connection.channel()
        channel.queue_declare(queue='borrow_queue')
        print("Successfully connected to RabbitMQ and declared queue.")
        break
    except pika.exceptions.AMQPConnectionError as e:
        print(f"Attempt {attempt + 1}/{retry_attempts}: RabbitMQ connection failed. Retrying in {retry_delay} seconds...")
        time.sleep(retry_delay)
else:
    print("Failed to connect to RabbitMQ after multiple attempts. Exiting...")
    exit(1)

# PostgreSQL Database Connection
db_user = os.getenv('POSTGRES_USER', 'postgres')
db_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
db_host = os.getenv('POSTGRES_HOST', 'database')
db_port = os.getenv('POSTGRES_PORT', '5432')
db_name = os.getenv('POSTGRES_DB', 'users_db')

def get_db_connection():
    try:
        return psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            cursor_factory=RealDictCursor
        )
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        exit(1)

def ensure_borrows_table_exists():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS borrows (
                studentid VARCHAR(20),
                bookid VARCHAR(20),
                borrow_date TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (studentid, bookid)
            );
        """)
        conn.commit()
        print("Ensured 'borrows' table exists.")
    except Exception as e:
        print(f"Error ensuring 'borrows' table exists: {e}")
    finally:
        cursor.close()
        conn.close()

# Call this function before starting RabbitMQ consumption
ensure_borrows_table_exists()

# Process Borrow Request
def process_borrow_request(ch, method, properties, body):
    data = json.loads(body)
    student_id = data.get("studentid")
    book_id = data.get("bookid")

    try:
        # Validate student existence via UserService
        user_response = requests.get(f'http://userservice:5002/users/{student_id}')
        if user_response.status_code == 404:
            print(f"Student {student_id} does not exist.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # Validate book existence via BookService
        book_response = requests.get(f'http://bookservice:5006/books/{book_id}')
        if book_response.status_code == 404:
            print(f"Book {book_id} does not exist.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check borrow count
        cursor.execute("SELECT COUNT(*) FROM borrows WHERE studentid = %s", (student_id,))
        borrow_count = cursor.fetchone()["count"]
        if borrow_count >= 5:
            print(f"Student {student_id} has already borrowed 5 books.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # Add borrow record
        cursor.execute("INSERT INTO borrows (studentid, bookid) VALUES (%s, %s)", (student_id, book_id))
        conn.commit()
        print(f"Borrow request processed for student {student_id}, book {book_id}.")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing borrow request: {e}")
    finally:
        cursor.close()
        conn.close()

# Consume RabbitMQ Messages
@app.route('/start-consume', methods=['POST'])
def start_consume():
    try:
        def consume():
            channel.basic_consume(queue='borrow_queue', on_message_callback=process_borrow_request, auto_ack=False)
            channel.start_consuming()

        # Start consuming in a new thread
        consume_thread = threading.Thread(target=consume)
        consume_thread.start()

        return jsonify({"message": "Started consuming borrow queue."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# List Books Borrowed by a Student
@app.route('/borrows/<studentid>', methods=['GET'])
def list_borrows(studentid):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM borrows WHERE studentid = %s", (studentid,))
        borrows = cursor.fetchall()
        return jsonify(borrows), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Return a borrowed book
@app.route('/return', methods=['DELETE'])
def return_book():
    data = request.json
    student_id = data.get("studentid")
    book_id = data.get("bookid")

    if not student_id or not book_id:
        return jsonify({"error": "studentid and bookid are required fields."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if the borrow record exists
        cursor.execute("SELECT * FROM borrows WHERE studentid = %s AND bookid = %s", (student_id, book_id))
        borrow = cursor.fetchone()
        if not borrow:
            return jsonify({"error": f"No borrow record found for student {student_id} and book {book_id}."}), 404

        # Delete the borrow record
        cursor.execute("DELETE FROM borrows WHERE studentid = %s AND bookid = %s", (student_id, book_id))
        conn.commit()

        return jsonify({"message": f"Book {book_id} successfully returned by student {student_id}."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    print("Starting Borrow Service...")
    app.run(host="0.0.0.0", port=5008)
