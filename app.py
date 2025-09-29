from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
app.secret_key='bababooey'


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
    username = db.Column(db.String(32), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    reservations = relationship('Reservation', backref='User')
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


    
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        books = search_books()
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

@app.route('/remove', methods=['GET', 'POST'])
def remove():
    if request.method=='POST':
        books = search_books()
        return render_template('remove.html', books=books)
    else:
        return render_template('remove.html')

@app.route('/remove/<int:id>')
def removeBook(id):
    bookToDelete = Book.query.get_or_404(id)
    try:
        db.session.delete(bookToDelete)
        db.session.commit()
        return redirect('/remove')
    except:
        return 'An error has occurred while removing book'

@app.route('/loginpage', methods=['GET', 'POST'])
def loginpage():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    user = User.query.filter_by(username=session['username']).first()
    reservations = Reservation.query.filter_by(userId=user.id)
    return render_template('dashboard.html', reservations=reservations, Book=Book)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['username'] = username
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user:
        return render_template("index.html", error="User already exists")
    else:
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = username
        return redirect(url_for('dashboard'))

@app.route('/borrow/<int:id>', methods=['GET', 'POST'])
def borrow(id):
    bookToBorrow = Book.query.get_or_404(id)
    userId = User.query.filter_by(username=session['username']).first().id
    borrowedTo = datetime.now() + timedelta(days=14)
    reservation = Reservation(bookId=id, userId=userId, borrowedTo=borrowedTo)
    try:
        db.session.add(reservation)
        bookToBorrow.reserved = True
        db.session.commit()
        return redirect('/')
    except:
        return 'Failed to borrow book'

@app.route('/return/<int:id>', methods=['GET','POST'])
def returnBook(id):
    reservationToReturn = Reservation.query.get_or_404(id)
    returnedBook = Book.query.filter_by(id=reservationToReturn.bookId).first()
    try:
        db.session.delete(reservationToReturn)
        returnedBook.reserved = False
        db.session.commit()
        return redirect('/dashboard')
    except:
        return 'Failed to return book'


def search_books(only_available = True):
    searchQuery = '%' + request.form['searchbook'] + '%'
    books = Book.query.where(Book.name.like(searchQuery), Book.reserved==False) if only_available else Book.query.where(Book.name.like(searchQuery))
    return books


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
