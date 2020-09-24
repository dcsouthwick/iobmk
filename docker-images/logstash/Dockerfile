FROM docker.elastic.co/logstash/logstash:7.4.2
RUN logstash-plugin install logstash-filter-prune
RUN logstash-plugin install logstash-input-stomp
RUN sed -i 's@xpack.monitoring.elasticsearch.hosts: \[ "http://elasticsearch:9200" \]@@' config/logstash.yml
#RUN echo "dead_letter_queue.enable: true" >> config/logstash.yml
#RUN echo "path.dead_letter_queue: /data/dead_letter_queue" >> config/logstash.yml
