FROM python:3.10-slim-bullseye

WORKDIR /code

COPY ./requirements.txt log_conf.yaml ./

RUN pip install --no-cache-dir -r requirements.txt

COPY lockoff lockoff

CMD ["uvicorn", "lockoff.main:app", "--log-config", "log_conf.yaml", "--host", "0.0.0.0", "--port", "80"]