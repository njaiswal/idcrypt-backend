FROM ubuntu:18.04

RUN set -ex && apt-get update

# Install python 3.7
RUN set -ex \
    && apt install software-properties-common -y \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt install python3.7 -y \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.7 1 \
    && python --version

# Install Node.js (v13.x) and npm (6.x)
RUN set -ex \
    && apt install curl -y \
    && curl -sL https://deb.nodesource.com/setup_13.x | bash - \
    && apt-get install -y nodejs \
    && node -v \
    && npm -v

# Update npm
RUN set -ex \
      && npm install --silent --no-progress -g npm

# Install serverless (1.63.0) and related plugins
RUN set -ex \
    && npm install -g serverless@1.63.0 \
    && npm install -g serverless-domain-manager@3.3.1 \
    && npm install -g serverless-offline@next \
    && npm install -g serverless-dynamodb-local

# Install java
RUN set -ex \
    && apt install openjdk-8-jdk openjdk-8-jre -y \
    && java -version

# Install moto
RUN set -ex \
    && apt install python3-pip -y \
    && pip3 install moto \
    && pip3 install flask \
    && moto_server -h

# Expose moto s3 server port
EXPOSE 4500
# Expose Dynamodb port
EXPOSE 8000
# Expose ELK ports
EXPOSE 9200
EXPOSE 9300
EXPOSE 5601

VOLUME /app

WORKDIR /app


