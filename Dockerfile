FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./script /code/script

COPY ./data /code/data

COPY ./app /code/app

COPY ./.env /code/.env