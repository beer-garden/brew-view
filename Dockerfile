FROM python:3.8-alpine
ARG VERSION
ENTRYPOINT ["brew-view"]

ENV BG_LOG_CONFIG_FILE=/logging-config.json

ADD dev_conf/logging-config.json /logging-config.json

RUN set -ex \
    && apk add --no-cache --virtual .build-deps \
       gcc make musl-dev libffi-dev openssl-dev \
    && pip install --no-cache-dir brew-view==$VERSION \
    && apk del .build-deps
