FROM python:3.11

RUN mkdir /app

WORKDIR /app

COPY main.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1

CMD ["nohup", "python", "main.py"]
