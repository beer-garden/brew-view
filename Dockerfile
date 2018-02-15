FROM python:2-alpine
ARG VERSION

ENV BG_LOG_CONFIG=/logging-config.json
ADD dev_conf/logging-config.json /logging-config.json

RUN set -ex \
    && apk add --no-cache --virtual .build-deps \
       gcc make musl-dev libffi-dev openssl-dev \
    && pip install --no-cache-dir brew-view==$VERSION \
    && apk del .build-deps

CMD ["brew-view"]

