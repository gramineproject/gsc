FROM ubuntu:22.04

RUN apt-get update

CMD ["echo", "\"Hello World! Let's check escaped symbols: < & > \""]
