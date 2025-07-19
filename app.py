import os
from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
from data_models import db, Author, Book
from datetime import datetime
from sqlalchemy.orm import joinedload
from sqlalchemy import or_

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"connect_args": {"check_same_thread": False}}

db.init_app(app)


@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            birth_date = request.form.get('birthdate')
            birth_date = datetime.strptime(birth_date, '%Y-%m-%d')
            date_of_death = request.form.get('date_of_death')
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
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            publication_year = int(request.form.get('publication_year'))
            isbn = int(request.form.get('isbn'))
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
    return render_template('home.html', books=db.session.query(Book).all(),
                           authors=db.session.query(Author).all())

@app.route('/sort', methods=['POST'])
def sort():
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
    search = request.form.get('search')
    books = db.session.query(Book).join(Author) \
        .options(joinedload(Book.author)).filter(or_(
        Book.title.ilike(f'%{search}%'),
        Author.name.ilike(f'%{search}%')
    )).all()

    return render_template('search.html', books=books)


@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
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

#with app.app_context():
 #   db.create_all()