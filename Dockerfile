FROM python:3.10.9

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

WORKDIR /app/src

CMD ["python3", "main.py"]
