From ubuntu:18.04

RUN apt-get -y update
RUN groupadd -r user && useradd -r -g user user
USER user

CMD ["echo", "\"Hello World! Let's check escaped symbols: < & > \""]
