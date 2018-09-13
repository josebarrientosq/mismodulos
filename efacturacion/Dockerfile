
FROM odoo:10.0

MAINTAINER danielvdmlfiis <danielvdmlfiis@gmail.com>
USER root

RUN set -x; \
        apt-get update \
        && apt-get install -y --no-install-recommends python-dev\
            build-essential \
            gcc \
            python-cffi \
            libxml2-dev \
            libxslt1-dev \
            libssl-dev \
            python-lxml \
            python-cryptography \
            python-openssl  \
            python-defusedxml \
            libleptonica-dev

RUN  pip install cryptography \
            ipaddress \
            signxml


