FROM python:3.10

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

ENV NAMEKO_CONFIG=config.yml

CMD ["nameko", "run", "--config", "config.yml", "service"]