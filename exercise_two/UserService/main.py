from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os
import json
import pika
import time

# Establish connection to RabbitMQ
credentials = pika.PlainCredentials(
    os.getenv("RABBITMQ_DEFAULT_USER", "guest"),
    os.getenv("RABBITMQ_DEFAULT_PASS", "guest")
)

retry_attempts = 10
retry_delay = 5

for attempt in range(retry_attempts):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host='rabbitmq',
                port=5672,
                credentials=credentials,
                heartbeat=120
            )
        )
        channel = connection.channel()
        print("Successfully connected to RabbitMQ.")
        break
    except pika.exceptions.AMQPConnectionError as e:
        print(f"Attempt {attempt + 1}/{retry_attempts}: RabbitMQ connection failed. Retrying in {retry_delay} seconds...")
        time.sleep(retry_delay)
else:
    print("Failed to connect to RabbitMQ after multiple attempts. Exiting...")
    exit(1)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='rabbitmq',
        port=5672,
        credentials=credentials,
        heartbeat=120  # Increase timeout to 120 seconds
    )
)
channel = connection.channel()

# Declare a queue
channel.queue_declare(queue='borrow_queue')

# Match these to docker-compose.yml values
db_user = os.getenv('POSTGRES_USER', 'postgres') 
db_password = os.getenv('POSTGRES_PASSWORD', 'postgres')  
db_host = os.getenv('POSTGRES_HOST', 'database') 
db_port = os.getenv('POSTGRES_PORT', '5432')  
db_name = os.getenv('POSTGRES_DB', 'users_db') 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'

    studentid = db.Column(db.String(20), primary_key=True)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    
    def to_dict(self):
        return {
            "studentid": self.studentid,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "email": self.email
        }
with app.app_context():
    db.create_all()


# CREATE users
@app.route('/users/add', methods=['POST'])
def create_user():
    data = request.json
    user = User(
         studentid=data['studentid'], 
         firstname=data['firstname'],
         lastname=data['lastname'], 
         email=data['email']
    )
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


# READ all users
@app.route('/users/all', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200


# READ a single user by ID
@app.route('/users/<studentid>', methods=['GET'])
def get_user(studentid:str):
    user = User.query.get(studentid)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict()), 200


# UPDATE a user by student_id
@app.route('/users/<studentid>', methods=['PUT'])
def update_user(studentid:str):
    user = User.query.get(studentid)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.json
    if 'firstname' in data:
        user.firstname = data['firstname']
    if 'lastname' in data:
        user.lastname = data['lastname']
    if 'email' in data:
        # Check if new email already exists for another user
        if User.query.filter(User.email == data['email'], User.studentid != studentid).first():
            return jsonify({"error": "Email already exists"}), 400
        user.email = data['email']
    db.session.commit()
    return jsonify(user.to_dict()), 200


# DELETE a user by student_id
@app.route('/users/<studentid>', methods=['DELETE'])
def delete_user(studentid:str):
    user = User.query.get(studentid)
    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"}), 200

@app.route('/borrow', methods=['POST'])
def borrow_book():
    data = request.json
    student_id = data.get('studentid')
    book_id = data.get('bookid')

    if not student_id or not book_id:
        return jsonify({"error": "studentid and bookid are required fields."}), 400

    # Publish a message to RabbitMQ
    message = {"studentid": student_id, "bookid": book_id}
    channel.basic_publish(
        exchange='',
        routing_key='borrow_queue',
        body=json.dumps(message)
    )
    return jsonify({"message": "Borrow request successfully posted!", "request": message}), 200



if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5002)
