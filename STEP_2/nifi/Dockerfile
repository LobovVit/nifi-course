FROM apache/nifi:1.28.1

USER root

# Создаём структуру, похожую на прод окружение
RUN mkdir -p /u01/nifi/nifi-current/lib \
    && mkdir -p /opt/nifi/.groovy/grapes

# Копируем jars
COPY drivers/postgresql-42.7.9.jar /opt/nifi/nifi-current/lib/postgresql-42.7.9.jar
COPY nifi-lib/ivy-2.5.3.jar /opt/nifi/nifi-current/lib/ivy-2.5.3.jar

# Дублируем в ожидаемый старый путь
RUN ln -s /opt/nifi/nifi-current/lib/postgresql-42.7.9.jar /u01/nifi/nifi-current/lib/postgresql-42.7.9.jar \
    && ln -s /opt/nifi/nifi-current/lib/ivy-2.5.3.jar /u01/nifi/nifi-current/lib/ivy-2.5.3.jar

# Права
RUN chmod -R 777 /opt/nifi/.groovy /u01/nifi

ENV JAVA_TOOL_OPTIONS="-Dgrape.root=/opt/nifi/.groovy/grapes"

USER root