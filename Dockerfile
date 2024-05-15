FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

COPY script /code/script

COPY data /code/data

COPY app /code/app

COPY .env /code/.env

COPY dev.sh /code/dev.sh

ENV LANGCHAIN_TRACING_V2=true \
    LANGCHAIN_API_KEY=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 \
    LANGCHAIN_PROJECT=chatbot \
# Vector Database path
    PERSISTENCE_PATH=../db/data_v2 \
# Port number
    BACKEND_PORT=9191 \
    FRONTEND_PORT=8080

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

RUN python3 ./script/create_database.py

CMD [ "bash", "dev.sh" ]