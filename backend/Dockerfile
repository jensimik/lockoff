FROM python:3.11-slim-bullseye

# get curl for health check
RUN apt-get update && apt-get install curl -y

WORKDIR /code

COPY ./requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY lockoff lockoff

CMD ["uvicorn", "lockoff.main:app", "--host", "0.0.0.0", "--port", "80"]