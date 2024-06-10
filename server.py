from flask import Flask, request, jsonify
import logging.config
from logging_config import logging_config
import os
import time
import datetime



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


def request_log_info(resource, verb):
    global request_counter
    request_counter += 1
    extra = {'request_number': request_counter}
    request_logger.info(f'Incoming request | #{request_counter} | resource: {resource} | HTTP Verb {verb}', extra=extra)

def request_log_debug(duration):
    extra = {'request_number': request_counter}
    request_logger.debug(f'request #{request_counter} duration: {duration}ms', extra=extra)

def book_log_info(message):
    extra = {'request_number': request_counter}
    books_logger.info(message, extra=extra)

def book_log_debug(message):
    extra = {'request_number': request_counter}
    books_logger.debug(message, extra=extra)

def book_log_error(message):
    extra = {'request_number': request_counter}
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
    app.run(debug=False, port=8574)
