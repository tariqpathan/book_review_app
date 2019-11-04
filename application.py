import os
import requests

from flask import Flask, jsonify, redirect, render_template, request, session
from flask_session import Session
from flask_bcrypt import Bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
bcrypt = Bcrypt(app)
"""Hardcoded Goodreads API key"""
goodreads_key = "yejP5xXK37CrW3r4Cjv0yg"

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()
    #surely there is an easier way for form verification than this
    #snakenest of if statements
    if request.method == "POST":
        if not request.form.get("username"):
            return error(400, "Please fill in the form")
        elif not request.form.get("password"):
            return error(400, "Please fill in the form")
        elif not request.form.get("confirmation"):
            return error(400, "Please fill in the form")
        elif request.form.get("password") != request.form.get("confirmation"):
            return error(400, "Passwords do not match")

        #Catch duplicate usernames
        try:
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
            {"username": request.form.get("username"),
            "hash": bcrypt.generate_password_hash(request.form.get("password")).decode("utf-8")})
        except IntegrityError:
            #session.rollback()
            return error(400, "Username taken")

        db.commit()

        #Add currently registered user into the session
        user_data = db.execute("SELECT * FROM users WHERE username=:username",
                                {"username": request.form.get("username")}).fetchall()
        session["user_id"] = user_data[0]["user_id"]

        return redirect("/")


    elif request.method == "GET":
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return error(400, "Please provide username")
        elif not request.form.get("password"):
            return error(400, "Please provide password")

        user_data = db.execute("SELECT * FROM users WHERE username=:username",
                            {"username": request.form.get("username")}).fetchall()

        if not user_data:
            return error(400, "User/Password incorrect")

        if bcrypt.check_password_hash((user_data[0]["hash"]), (request.form.get("password"))) == True:
            session["user_id"] = user_data[0]["user_id"]
            return redirect("/")
        else:
            return error(400, "User/Password incorrect")
    elif request.method == "GET":
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()

    return redirect("/")


@app.route("/search", methods=["POST"])
def search():
    if request.method == "POST":
        #need to modify to ignore case
        query = request.form.get("search")
        wildcard_query = "%" + query + "%"

        #will use casting because input via form will come back as string
        try:
            int(query)
            rows = db.execute("SELECT * FROM books WHERE"
                            " CAST(year AS VARCHAR(4)) IILIKE :query OR"
                            " isbn ILIKE :query", {"query": wildcard_query}).fetchmany(20)

        except ValueError:
            #if query cannot be cast as an int, it isn't a year
            rows = db.execute("SELECT * FROM books WHERE"
                            " title ILIKE :query OR"
                            " author ILIKE :query OR"
                            " isbn ILIKE :query", {"query": wildcard_query}).fetchmany(20)

        #print(rows)

        return render_template("search_results.html", rows=rows)

    else:
        return render_template("index.html")

@app.route("/bookpage/<string:isbn>", methods=["GET", "POST"])
def bookpage(isbn):
    print(isbn)
    if request.method == "POST":
        try:
            db.execute("INSERT INTO reviews (user_id, isbn, rating, comments) VALUES (:user_id, :isbn, :rating, :comments)",
            {"user_id":session.get("user_id"), "isbn": isbn,
            "rating": request.form.get("rating"),
            "comments": request.form.get("comments")})
        except IntegrityError:
            db.rollback()
            db.execute("UPDATE reviews SET (rating, comments) = (:rating, :comments) WHERE user_id=:user_id AND isbn=:isbn", {"rating": request.form.get("rating"),
            "comments": request.form.get("comments"),
            "user_id": session.get("user_id"), "isbn": isbn})
        db.commit()

        return redirect("/")

    elif request.method == "GET":
        book = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn": isbn}).fetchone()

        if book is None:
            return error(404, "No books found")
        review_data = (goodreads_reviews(isbn)["books"][0])

        user_id = session.get("user_id")
        if user_id is None:
            return render_template("bookpage.html", book=book, review_data=review_data)
        
        else:
            reviews = db.execute("SELECT * FROM reviews WHERE user_id=:user_id "
                                "AND isbn=:isbn", {"user_id": session["user_id"],
                                "isbn": isbn}).fetchone()

            return render_template("bookpage.html", book=book, reviews=reviews, user_id=user_id, review_data=review_data)

def goodreads_reviews(isbn):
    goodreads_data = requests.get("https://www.goodreads.com/book/review_counts.json", 
    params={"key": goodreads_key, "isbns": isbn})
    return (goodreads_data.json())


@app.route("/api/<string:isbn>")
def api(isbn):
    rows = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn": isbn}).fetchall()
    print(rows)
    if not rows:
        return error(404, "No book with that isbn found")
    book = dict(rows[0])
    book["review_count"] = goodreads_reviews(isbn)["books"][0]["work_ratings_count"]
    book["average_score"] = goodreads_reviews(isbn)["books"][0]["average_rating"]
    json_book = jsonify(book)
    return json_book


@app.route("/myreviews", methods=["GET"])
def myreviews():
    if session.get("user_id") is None:
        return redirect("/login")
    else:
        reviews = db.execute("SELECT * FROM reviews JOIN books ON reviews.isbn = books.isbn"
        " WHERE user_id=:user_id", {"user_id": session.get("user_id")}).fetchall()
        
        return render_template("myreviews.html", reviews=reviews)    


@app.route("/error")
def error(code, message):
    return render_template("error.html", code=code, message=message)