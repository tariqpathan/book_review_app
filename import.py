import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = sessionmaker(bind=engine)()


books_file = open("books.csv")
reader = csv.reader(books_file)

for ISBN, title, author, year in reader:
    try:
        int_year = int(year)
        db.execute("INSERT INTO books (ISBN, title, author, year)"
                "VALUES (:ISBN, :title, :author, :year)",
                {"ISBN": ISBN, "title": title, "author": author, "year": int_year})
    except ValueError:
        pass
    db.commit()
