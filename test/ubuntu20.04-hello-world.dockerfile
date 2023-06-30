From ubuntu:20.04

RUN apt-get update

CMD ["echo", "\"Hello World! Let's check escaped symbols: < & > \""]
