FROM fsfe/pipenv:alpine-3.13 AS pipenv-env

WORKDIR /listen_and_repeat_bot

COPY Pipfile ./
COPY Pipfile.lock ./
RUN pipenv lock -r -d > requirements.txt



FROM python:3.8.15-buster
LABEL MAINTAINER=github.com/mdraevich
LABEL SERVICE=bot_handler

WORKDIR /listen_and_repeat_bot

COPY --from=pipenv-env /listen_and_repeat_bot/requirements.txt ./
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "main.py"]