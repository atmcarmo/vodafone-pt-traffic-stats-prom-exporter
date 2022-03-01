FROM python:3.11.0a5-bullseye

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip 

RUN python -m pip install requests
RUN python -m pip install prometheus_client

WORKDIR /app
COPY exporter.py /app/

CMD ["python", "exporter.py"]

EXPOSE 8081