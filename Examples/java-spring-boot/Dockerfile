FROM openjdk:11

RUN apt-get update && \
    apt-get install -y openjdk-11-jdk

COPY spring-boot-web-service/build/libs/spring-boot-web-service-0.0.1-SNAPSHOT.jar .

ENTRYPOINT ["java", "-jar", "/spring-boot-web-service-0.0.1-SNAPSHOT.jar"]
