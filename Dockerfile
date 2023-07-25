FROM python:3.11.4-slim-bookworm as build-image

WORKDIR /usr/local/bin/deployment

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y curl ca-certificates gnupg gcc g++ make libffi-dev git cargo pkg-config libhdf5-dev

COPY ./ /tmp/build

RUN  (cd /tmp/build \
     && python3 -m venv py3env-dev \
     && . py3env-dev/bin/activate \
     && python3 -m pip install -U -r requirements_dev.txt \
     && python3 setup.py bdist_wheel)


RUN  export APP_HOME=/usr/local/bin/deployment \
     && (cd $APP_HOME \
         && python3 -m venv py3env \
         && . py3env/bin/activate \
         && python3 -m pip install -U pip \
         && python3 -m pip install -U setuptools \
         && python3 -m pip install -U wheel \
         && python3 -m pip install -U /tmp/build/dist/*.whl)


FROM python:3.11.4-slim-bookworm

ENV  PYTHONPATH=/usr/local/bin/deployment

WORKDIR /usr/local/bin/deployment

COPY --from=build-image /usr/local/bin/deployment/ ./

RUN  groupadd -r appgroup \
     && useradd -r -G appgroup -d /home/appuser appuser \
     && install -d -o appuser -g appgroup /usr/local/bin/deployment/logs

USER  appuser
CMD ["/usr/local/bin/deployment/py3env/bin/python3", "-m", "dataset_image_converter"]
