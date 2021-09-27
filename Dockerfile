FROM fedora:34 

RUN dnf install -y python3-pip which \
&& dnf clean all \
&& pip3 install pipenv

VOLUME /backups

COPY . /archivist

RUN touch /archivist/archivist.yml

WORKDIR /archivist

RUN pipenv install 

ENTRYPOINT ["/archivist/bin/archivist.sh"]

