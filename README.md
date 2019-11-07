# Project 1

Web Programming with Python and JavaScript

Premise

This was a project that used a python server using Flask, with a SQL database, dynamically generating HTML pages depending on the user and their input.

I built this project firstly, because it was a requirement of the CS50 web course. However, it has allowed me to understand some of the abstractions that take place when we use frameworks at higher levels, for example in Django or ORMs. 

Motivation

The premise of the project is a book review site that pulls information from Goodreads as well as storing ratings given by individual users along with a text comment. 

The database stores about 5000 books, so creating an individual page for each book is not feasible. Instead, using flask and jinja2 we can dynamically generate a "bookpage" that retrieves details from the SQL backend and Goodreads.

I enjoyed learning how the database talks with flask and how that creates a html page. I've recently learned about ORMs and issues with writing raw SQL which is what I used in this project (as instructed). 

Functions

The website allows a user to register and login with a unique username. Basic if statements are used to check validity - no libraries are used for this.

Searching is allowed which uses wildcard characters and an ILIKE statement for SQL, returning the first 20 results. Each result dynamically generates a link for the individual book which provides very simple data on the book:
-Title
-Author
-Year it was first published
-Goodreads review count
-Goodreads average review

If the user is logged in and has previously left reviews, they can also see this.