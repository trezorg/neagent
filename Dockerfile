FROM python:3-stretch

ENV \
    WORKDIR='/neagent' \
    USER='neagent' \
    DATA_DIR='/data'


MAINTAINER Igor Nemilentsev <trezorg@gmail.com>

RUN \
    apt-get update -q && \
    apt-get install -yqq unixodbc unixodbc-dev libsqliteodbc && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -u 1000 -U -M -o ${USER} && \
    mkdir -p ${DATA_DIR} && \
    chown -R ${USER} ${DATA_DIR}

RUN \
    pip install -U git+https://github.com/trezorg/neagent.git

USER ${USER}
WORKDIR ${DATA_DIR}
ENTRYPOINT ["neagent"]
