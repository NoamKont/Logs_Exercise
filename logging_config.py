logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s %(levelname)s: %(message)s | request #%(request_number)d ',
            'datefmt': '%d-%m-%Y %H:%M:%S',

        },
    },
    'handlers': {
        'requests_file_handler': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/requests.log',
            'formatter': 'default',
        },
        'books_file_handler': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/books.log',
            'formatter': 'default',
        },
        'console_handler': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
    },
    'loggers': {
        'request-logger': {
            'handlers': ['requests_file_handler', 'console_handler'],
            'level': 'INFO',
            'propagate': False,
        },
        'books-logger': {
            'handlers': ['books_file_handler'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}
