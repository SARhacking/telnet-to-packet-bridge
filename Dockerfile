FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ax25-tools \
        ax25-apps \
        iproute2 \
        net-tools \
        kmod \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY bridge.py /app/bridge.py

ENTRYPOINT ["python3", "/app/bridge.py"]
