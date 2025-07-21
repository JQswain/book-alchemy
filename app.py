import os
from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
from data_models import db, Author, Book
from datetime import datetime
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from isbnlib import is_isbn10, is_isbn13

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"connect_args": {"check_same_thread": False}}

db.init_app(app)

#with app.app_context(): #commented out after initializing the table
   #db.create_all()

def validate_isbn(isbn: str) -> bool:
    """checks if the given ISBN is valid"""
    isbn = isbn.replace('-', '').replace(' ', '')
    return is_isbn10(isbn) or is_isbn13(isbn)


@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    """Handles the addition of a new author via a web form. With 'Get', it shows the form, and 'post'
    it sends the data and reloads the original web form"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            birth_date = request.form.get('birthdate')
            if not isinstance(birth_date, datetime):
                raise TypeError("Birthdate must be a datetime object")
            birth_date = datetime.strptime(birth_date, '%Y-%m-%d')
            date_of_death = request.form.get('date_of_death')
            if not isinstance(date_of_death, datetime):
                raise TypeError("Date of death must be a datetime object")
            date_of_death = datetime.strptime(date_of_death, '%Y-%m-%d')

            author = Author(name, birth_date, date_of_death)
            db.session.add(author)
            db.session.commit()

            return render_template("add_author.html", author=author)

        except Exception as e:
            db.session.rollback()
            return f"Error: {e}", 500

    return render_template("add_author.html", author=None)

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    """Handle the addition of a new book via a web form. With Get, it shows the form, and post
    it sends the data and reloads the original web form"""
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            publication_year = int(request.form.get('publication_year'))
            isbn = (request.form.get('isbn', '').strip())
            if not validate_isbn(isbn):
                raise TypeError("ISBN must be a valid ISBN")
            author_id = int(request.form.get('author_id'))

            book = Book(title=title, publication_year=publication_year, isbn=isbn,
                        author_id=author_id)

            db.session.add(book)
            db.session.commit()


            return render_template("add_book.html", authors=db.session.query(Author).all(),
                                   book=book)

        except Exception as e:
            db.session.rollback()
            return f"Error: {e}", 500

    return render_template("add_book.html", authors=db.session.query(Author).all(),
                           book=None)

@app.route('/', methods=['GET'])
def home():
    """Handles the home page, shows all books in the library, and allows for search and sort functions"""
    return render_template('home.html', books=db.session.query(Book).all(),
                           authors=db.session.query(Author).all())

@app.route('/sort', methods=['POST'])
def sort():
    """Handles the sorting page, uses parameters from the homepage form to know how to sort them"""
    author_id = request.form.get('author_id')
    book_title = request.form.get('book_title')

    books = db.session.query(Book)

    if author_id:
        books = books.filter_by(author_id=int(author_id))
    elif book_title:
        books = books.filter_by(title=book_title)

    return render_template('home.html', books=books.all(),
                           authors=db.session.query(Author).all())


@app.route('/search', methods=['POST'])
def search():
    """Handles the search from the homepage and loads the relevant books"""
    search_request = request.form.get('search')
    books = db.session.query(Book).join(Author) \
        .options(joinedload(Book.author)).filter(or_(
        Book.title.ilike(f'%{search_request}%'),
        Author.name.ilike(f'%{search_request}%')
    )).all()

    return render_template('search.html', books=books)


@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    """Deletes the book from the database"""
    book = db.session.query(Book).get(book_id)
    message = f"{book.title} deleted successfully"
    db.session.delete(book)
    db.session.commit()
    code = 304

    return render_template('home.html',
                           books=db.session.query(Book).all(),
                           authors=db.session.query(Author).all(),
                           message=message, code=code)

@app.route('/author/delete', methods=['POST'])
def delete_author():
    """Deletes the author from the database, after checking if there are no books left by that author"""
    author_id = request.form.get('author_id')
    books = db.session.query(Book).filter(Book.author_id == author_id).all()
    author = db.session.query(Author).filter(Author.id == author_id).first()

    if not author:
        message = "Author not found."
    elif books:
        message = f"Author '{author.name}' cannot be deleted because they have books."
    else:
        db.session.delete(author)
        db.session.commit()
        message = f"Author '{author.name}' deleted successfully."

    return render_template(
        'home.html',
        books=db.session.query(Book).all(),
        authors=db.session.query(Author).all(),
        message=message
    )




if __name__ == '__main__':
    app.run(port=5002, debug=True)

