FROM docker.elastic.co/logstash/logstash-oss:6.5.0

COPY ./rootfs/ /

USER root

RUN chown -v logstash:logstash /usr/share/logstash/pipeline/logstash.conf \
    && chmod -v go-w /usr/share/logstash/pipeline/logstash.conf

USER logstash

EXPOSE 5044/tcp

# vim: ft=dockerfile
