from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import os

# Match these to docker-compose.yml values
db_user = os.getenv('POSTGRES_USER', 'postgres')
db_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
db_host = os.getenv('POSTGRES_HOST', 'database')
db_port = os.getenv('POSTGRES_PORT', '5432')
db_name = os.getenv('POSTGRES_DB', 'books_db')

# Build the database URL
db_url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

# Retry mechanism to handle database unavailability
import time
max_retries = 5
for attempt in range(max_retries):
    try:
        engine = create_engine(db_url)
        if not database_exists(engine.url):
            create_database(engine.url)
        break
    except Exception as e:
        print(f"Database connection failed ({attempt + 1}/{max_retries}): {e}")
        time.sleep(5)

# Flask app setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Book model
class Book(db.Model):
    __tablename__ = 'books'

    bookid = db.Column(db.String(20), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "bookid": self.bookid,
            "title": self.title,
            "author": self.author,
            "year": self.year
        }

# Ensure tables exist
with app.app_context():
    db.create_all()
    print("Ensured 'books' table exists in the database.")


# CREATE book
@app.route('/books/add', methods=['POST'])
def create_book():
    data = request.json
    book = Book(
        bookid=data['bookid'],
        title=data['title'],
        author=data['author'],
        year=data['year']
    )
    db.session.add(book)
    db.session.commit()
    return jsonify(book.to_dict()), 201

# READ all books
@app.route('/books/all', methods=['GET'])
def get_books():
    books = Book.query.all()
    return jsonify([book.to_dict() for book in books]), 200

# READ a single book by bookid
@app.route('/books/<bookid>', methods=['GET'])
def get_book(bookid: str):
    book = Book.query.get(bookid)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    return jsonify(book.to_dict()), 200

# UPDATE a book by bookid
@app.route('/books/<bookid>', methods=['PUT'])
def update_book(bookid: str):
    book = Book.query.get(bookid)
    if not book:
        return jsonify({"error": "Book not found"}), 404

    data = request.json
    if 'title' in data:
        book.title = data['title']
    if 'author' in data:
        book.author = data['author']
    if 'year' in data:
        book.year = data['year']

    db.session.commit()
    return jsonify(book.to_dict()), 200

# DELETE a book by bookid
@app.route('/books/<bookid>', methods=['DELETE'])
def delete_book(bookid: str):
    book = Book.query.get(bookid)
    if not book:
        return jsonify({"error": "Book not found"}), 404

    db.session.delete(book)
    db.session.commit()
    return jsonify({"message": "Book deleted successfully"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006)
