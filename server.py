from flask import Flask, request, jsonify
import logging.config
from logging_config import logging_config
import os
import time
import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Replace with your credentials and host information
host = "localhost"  # Use the Docker host IP if connecting from another machine
port = 27017        # Default MongoDB port

# MongoDB connection URI
uri = f"mongodb://{host}:{port}/"

# Create a client
try:
    # Connect to MongoDB
    client = MongoClient(uri)

    # Ping the server to check the connection
    client.admin.command("ping")
    print("Connection successful!")

except ConnectionFailure as e:
    print(f"Connection failed: {e}")


# Access a specific database
db = client["books"]  # Replace 'my_database' with your database name
print(db)
# Access a collection
collection = db["books"]  # Replace 'my_collection' with your collection name
print(collection)

all_records = collection.find()
print(list(all_records))
for record in all_records:
    print(record)


import psycopg2

# Database connection parameters
host = "localhost"  # or your database server's address
database = "books"
user = "postgres"
password = "docker"
port = 5432  # default PostgreSQL port

try:
    # Establishing the connection
    connection = psycopg2.connect(
        host=host,
        database=database,
        user=user,
        password=password,
        port=port
    )

    # Create a cursor object
    cursor = connection.cursor()

    # Query to fetch all data from the 'books' table
    cursor.execute("SELECT * FROM books;")

    # Fetch all rows from the result of the query
    rows = cursor.fetchall()

    # Print the data in the 'books' table
    for row in rows:
        print(row)

except psycopg2.Error as e:
    print(f"Error while connecting to PostgreSQL: {e}")

finally:
    # Close the cursor and connection
    if cursor:
        cursor.close()
    if connection:
        connection.close()
        print("PostgreSQL connection is closed")

request_counter = 0

os.makedirs('logs', exist_ok=True)

app = Flask(__name__)

logging.config.dictConfig(logging_config)
request_logger = logging.getLogger('request-logger')
books_logger = logging.getLogger('books-logger')


class bookStore:
    def __init__(self):
        self.books = []
        self.bookGenre = ['SCI_FI', 'NOVEL', 'HISTORY', 'MANGA', 'ROMANCE', 'PROFESSIONAL']
        self.booksNumber = 0

    def findBook(self, filter: dict):
        res = self.books
        if filter.get('genres') is not None:
            for genre in filter['genres'].split(","):
                if genre not in self.bookGenre:
                    return -1

        for argument in filter.keys():
            if argument == "author":
                res = [book for book in res if (book.Author).lower() == (filter["author"]).lower()]
            elif argument == "price-bigger-than":
                res = [book for book in res if book.Price > int(filter["price-bigger-than"])]
            elif argument == "price-less-than":
                res = [book for book in res if book.Price < int(filter["price-less-than"])]
            elif argument =="year-bigger-than":
                res = [book for book in res if book.PrintYear > int(filter["year-bigger-than"])]
            elif argument == "year-less-than":
                res = [book for book in res if book.PrintYear < int(filter["year-less-than"])]
            elif argument == "genres":
                temp =[]
                for book in res:
                    for kind in book.Genre:
                        if kind in filter["genres"].split(","):
                                temp.append(book)
                                continue
                res = temp

        return res

    def addBook(self,book):
        self.books.append(book)
        self.booksNumber += 1

    def validYear(self, year):
        if (1940 <= year <= 2100):
            return True
        else:
            return False

    def checkPrice(self, price):
        if (price > 0):
            return True
        else:
            return False

    def isBookExists(self, bookName):
        if any(bookName.lower() == book.Title.lower() for book in self.books):
            return True
        else:
            return False


class book:
    def __init__(self, id, title, author, year, price, genre):
        self.Id = id
        self.Title = title
        self.Author = author
        self.PrintYear = year
        self.Price = price
        self.Genre = genre

    def to_json(self):
        return {
            "id": self.Id,
            "title": self.Title,
            "author": self.Author,
            "price": self.Price,
            "year": self.PrintYear,
            "genres": self.Genre
        }

def time_stemp():
    t = datetime.datetime.now()
    s = t.strftime('%d-%m-%Y %H:%M:%S.%f')
    return s[:-3]
def request_log_info(resource, verb):
    global request_counter
    request_counter += 1
    time = time_stemp()
    extra = {'request_number': request_counter,
             'time': time
             }
    request_logger.info(f'Incoming request | #{request_counter} | resource: {resource} | HTTP Verb {verb}', extra=extra)

def request_log_debug(duration):
    t = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S.%f')[:3]
    time = time_stemp()
    extra = {'request_number': request_counter,
             'time': time
             }
    request_logger.debug(f'request #{request_counter} duration: {duration}ms', extra=extra)

def book_log_info(message):
    time = time_stemp()
    extra = {'request_number': request_counter,
             'time': time
             }
    books_logger.info(message, extra=extra)

def book_log_debug(message):
    time = time_stemp()
    extra = {'request_number': request_counter,
             'time': time
             }
    books_logger.debug(message, extra=extra)

def book_log_error(message):
    time = time_stemp()
    extra = {'request_number': request_counter,
             'time': time
             }
    books_logger.error(message, extra=extra)


bookStore = bookStore()


@app.route('/books/health', methods=['GET'], endpoint='health')
def Health():
    return 'OK', 200


@app.route('/book', methods=['POST'], endpoint='CreatNewBook')
def CreatNewBook():
    start_time = time.time()
    request_log_info('/book', 'POST')
    data = request.get_json()
    if (bookStore.isBookExists(data['title'])):
        error = f"Error: Book with the title [{data['title']}] already exists in the system"
        response = jsonify({"errorMessage": error})
        book_log_error(error)
        return response, 409

    elif (not bookStore.validYear(data['year'])):
        error = f"Error: Can’t create new Book that its year [{data['year']}] is not in the accepted range [1940 -> 2100]"
        response = jsonify({"errorMessage": error})
        book_log_error(error)
        return response, 409

    elif (not bookStore.checkPrice(data['price'])):
        error = f"Error: Can’t create new Book with negative price"
        response = jsonify({"errorMessage": error})
        book_log_error(error)
        return response, 409

    else:
        newBook = book(bookStore.booksNumber + 1, data['title'], data['author'], data['year'], data['price'], data['genres'])
        book_log_info(f'Creating new Book with Title [{data["title"]}]')
        book_log_debug(f"Currently there are {len(bookStore.books)} Books in the system. New Book will be assigned with id {bookStore.booksNumber + 1}")
        bookStore.addBook(newBook)
        response = jsonify({"result": bookStore.booksNumber})

        duration = (time.time() - start_time) * 1000
        request_log_debug(duration)
        return response, 200


@app.route('/books/total', methods=['GET'], endpoint='getTotalBooks')
def getTotalBooks():
    start_time = time.time()
    request_log_info('/books/total', 'GET')
    query_params = dict(request.args)
    numOfBooks = bookStore.findBook(query_params)
    if numOfBooks == -1:
        return '', 400
    else:
        book_log_info(f'Total Books found for requested filters is {len(numOfBooks)}')
        duration = (time.time() - start_time) * 1000
        request_log_debug(duration)
        return jsonify({"result": len(numOfBooks)}), 200


@app.route('/books', methods=['GET'], endpoint='getBooksData')
def getBooksData():
    start_time = time.time()
    request_log_info('/books', 'GET')
    query_params = dict(request.args)
    books = bookStore.findBook(query_params)
    if books == -1:
        empty_array = []
        return jsonify({"result": empty_array}), 200
    book_log_info(f'Total Books found for requested filters is {len(books)}')
    sorted_books = sorted(books, key=lambda x: x.Title)
    sorted_books_json = [book_obj.to_json() for book_obj in sorted_books]
    duration = (time.time() - start_time) * 1000
    request_log_debug(duration)
    return jsonify({"result": sorted_books_json}), 200


@app.route('/book', methods=['GET'], endpoint='getSingleBookData')
def getBookData():
    start_time = time.time()
    request_log_info('/book', 'GET')
    id_param = int(request.args.get('id'))
    for book in bookStore.books:
        if book.Id == id_param:
            book_log_debug(f'Fetching book id {id_param} details')
            duration = (time.time() - start_time) * 1000
            request_log_debug(duration)
            return jsonify({"result": book.to_json()}), 200
    book_log_error(f"Error: no such Book with id {id_param}")
    duration = (time.time() - start_time) * 1000
    request_log_debug(duration)
    return jsonify({"errorMessage": f"Error: no such Book with id {id_param}"}), 404


@app.route('/book', methods=['PUT'], endpoint='updateBookprice')
def updateBookData():
    start_time = time.time()
    request_log_info('/book', 'PUT')
    id_param = int(request.args.get('id'))
    if id_param <= 0:
        book_log_error(f"Error: price update for book [{id_param}] must be a positive integer")
        return jsonify({"errorMessage": f"Error: price update for book [{id_param}] must be a positive integer"}), 409
    for book in bookStore.books:
        if book.Id == id_param:
            book_log_info(f'Update Book id [{id_param}] price to {int(request.args.get("price"))}')
            oldPrice = book.Price
            book.Price = int(request.args.get('price'))
            book_log_debug(f'Book [{book.Title}] price change: {oldPrice} --> {book.Price}')
            duration = (time.time() - start_time) * 1000
            request_log_debug(duration)
            return jsonify({"result": oldPrice}), 200
    book_log_error(f"Error: no such Book with id {id_param}")
    duration = (time.time() - start_time) * 1000
    request_log_debug(duration)
    return jsonify({"errorMessage": f"Error: no such Book with id {id_param}"}), 404


@app.route('/book', methods=['DELETE'], endpoint='deleteBook')
def deleteBookData():
    start_time = time.time()
    request_log_info('/book', 'DELETE')
    id_param = int(request.args.get('id'))
    for book in bookStore.books:
        if book.Id == id_param:
            book_log_info(f'Removing book [{book.Title}]')
            removedBook = book
            bookStore.books.remove(book)
            book_log_debug(f'After removing book [{removedBook.Title}] id: [{removedBook.Id}] there are {len(bookStore.books)} books in the system')
            duration = (time.time() - start_time) * 1000
            request_log_debug(duration)
            return jsonify({"result": len(bookStore.books)}), 200
    book_log_error(f"Error: no such Book with id {id_param}")
    duration = (time.time() - start_time) * 1000
    request_log_debug(duration)
    return jsonify({"errorMessage": f"Error: no such Book with id {id_param}"}), 404

@app.route('/logs/level', methods=['GET'], endpoint='Gets The Current Level')
def getLogsLevel():
    start_time = time.time()
    request_log_info('/logs/level', 'GET')

    name = request.args.get('logger-name')
    if name == 'request-logger':
        level = request_logger.level
        level_string = logging.getLevelName(level)
    elif name == 'books-logger':
        level = books_logger.level
        level_string = logging.getLevelName(level)
    else:
        duration = (time.time() - start_time) * 1000
        request_log_debug(duration)
        return jsonify({"errorMessage": f"Error: no such logger"}), 404

    duration = (time.time() - start_time) * 1000
    request_log_debug(duration)
    return level_string, 200

@app.route('/logs/level', methods=['PUT'], endpoint='Set The Current Level')
def setLogsLevel():
    start_time = time.time()
    request_log_info('/logs/level', 'PUT')

    name = request.args.get('logger-name')
    level = request.args.get('logger-level').upper()
    levels = {
        'ERROR': logging.ERROR,
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
    }
    if name == 'request-logger':
        request_logger.setLevel(levels[level])
    elif name == 'books-logger':
        books_logger.setLevel(levels[level])
    else:
        duration = (time.time() - start_time) * 1000
        request_log_debug(duration)
        return jsonify({"errorMessage": f"Error: no such logger"}), 404

    duration = (time.time() - start_time) * 1000
    request_log_debug(duration)
    return jsonify({"result": level}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=8574)
