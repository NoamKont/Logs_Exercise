FROM python:3.10

WORKDIR /server
COPY . .
RUN pip install flask
EXPOSE 8574
CMD ["python","./server.py"]
