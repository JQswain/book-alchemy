from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    date_of_death = db.Column(db.Date, nullable=False)

    books = db.relationship('Book', backref='author', lazy=True)

    def __init__(self, name, birth_date, date_of_death):
        self.name = name
        self.birth_date = birth_date
        self.date_of_death = date_of_death

    def __repr__(self):
        return (f'<Author {self.name}>'
                f'<Born: {self.birth_date}>'
                f'<Died: {self.date_of_death}>')

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    publication_year = db.Column(db.Integer, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)

    def __init__(self, isbn, title, publication_year, author_id):
        self.isbn = isbn
        self.title = title
        self.publication_year = publication_year
        self.author_id = author_id

    def __repr__(self):
        return (f'<Title: {self.title}>'
                f'<Publication Year: {self.publication_year}>'
                )



