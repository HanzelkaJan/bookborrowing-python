from datetime import datetime

from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
app.app_context().push()

class Reservation(db.Model):
    __tablename__ = "Reservation"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bookId = db.Column(db.Integer, ForeignKey('Book.id'))
    userId = db.Column(db.Integer, ForeignKey('User.id'))
    borrowedFrom = db.Column(db.DateTime, default=datetime.now)
    borrowedTo = db.Column(db.DateTime)

class Book(db.Model):
    __tablename__ = "Book"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String(256))
    name = db.Column(db.String(256))
    author = db.Column(db.String(256))
    reservations = relationship('Reservation', backref='Book')
    reserved = db.Column(db.Integer, default=0)
    
class User(db.Model):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    firstName = db.Column(db.String(256))
    lastName = db.Column(db.String(256))
    email = db.Column(db.String(256))
    reservations = relationship('Reservation', backref='User')
    
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        searchQuery = '%'+request.form['searchbook']+'%'
        books = Book.query.where(Book.name.like(searchQuery))
        return render_template('index.html', books=books)
    else:
        return render_template('index.html')

@app.route('/add', methods=['POST', 'GET'])
def add():
    if request.method == 'POST':
        isbn = request.form['isbn']
        name = request.form['bookname']
        author = request.form['author']
        newBook = Book(isbn=isbn, name=name, author=author)
        try:
            db.session.add(newBook)
            db.session.commit()
            return redirect('/add')
        except:
            return 'Failed to add book'
    else:
        books = Book.query.all()
        return render_template('add.html', books=books)

if __name__ == "__main__":
    app.run(debug=True)
