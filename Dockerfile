FROM python:3.10

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["nameko", "run", "--config", "config.yml", "service"]