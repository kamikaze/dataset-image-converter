FROM --platform=$TARGETPLATFORM python:3.13-slim-bookworm as build-image

WORKDIR /app

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y curl ca-certificates gnupg gcc g++ make libffi-dev git cargo pkg-config libhdf5-dev

COPY requirements.txt .
RUN python3 -m pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt


FROM --platform=$TARGETPLATFORM python:3.13-slim-bookworm

ENV PYTHONPATH=/app

WORKDIR /app

COPY --from=build-image /app/wheels /wheels

RUN pip install --no-cache /wheels/*

RUN  groupadd -r appgroup \
     && useradd -r -G appgroup -d /home/appuser appuser \
     && install -d -o appuser -g appgroup /usr/local/app/logs

USER  appuser

COPY --chown=appuser src/ ./

CMD ["python3", "-m", "dataset_image_converter"]
