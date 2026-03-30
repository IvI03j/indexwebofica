FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir flask || true

ENV PORT=5000

CMD ["python3", "-m", "app"]
