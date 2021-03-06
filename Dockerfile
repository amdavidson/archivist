FROM debian:stable

RUN apt-get update && apt-get install -y python3-pip && apt-get clean && pip3 install pipenv

VOLUME /backups

COPY . /archivist

RUN touch /archivist/archivist.yml

WORKDIR /archivist

RUN pipenv install 

ENTRYPOINT ["/archivist/bin/archivist.sh"]

