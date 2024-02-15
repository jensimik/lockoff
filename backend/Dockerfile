FROM python:3.12-slim-bookworm

# get curl for health check and libpango for weazyprint and sqlite3 for db
RUN apt-get update && \
    apt-get install curl libpango-1.0-0 libpangoft2-1.0-0 sqlite3 libsqlite3-dev -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY ./requirements.txt log_conf.yaml ./

RUN pip install --no-cache-dir -r requirements.txt

COPY lockoff lockoff

CMD ["uvicorn", "lockoff.main:app", "--log-config", "log_conf.yaml", "--host", "0.0.0.0", "--port", "80"]