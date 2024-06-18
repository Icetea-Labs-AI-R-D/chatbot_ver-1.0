FROM python:3.10

WORKDIR /code

COPY ./requirements.txt ./requirements.txt

COPY data ./data

COPY app ./app

COPY .env ./.env

COPY create_database.py ./create_database.py

COPY dev.sh ./dev.sh

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

EXPOSE 9191

CMD [ "bash", "dev.sh" ]