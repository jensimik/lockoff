FROM python:3.10-slim-bullseye

WORKDIR /code

COPY ./requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY lockoff lockoff

CMD ["uvicorn", "lockoff.main:app", "--host", "0.0.0.0", "--port", "80"]