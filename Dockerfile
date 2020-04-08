FROM debian:stable

RUN apt-get update && apt-get install -y python3-pip && apt-get clean && pip3 install pipenv

VOLUME /backups

COPY . /archivist

WORKDIR /archivist

RUN pipenv install 

CMD /archivist/bin/archivist.sh backup 

