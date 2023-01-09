# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM ubuntu:latest

RUN DD_INSTALL_ONLY=true DD_SITE="datadoghq.com" bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script_agent7.sh)"

RUN apt-get update -y
RUN apt-get install -y python3 pip apt-transport-https curl gnupg

# Setting up the Datadog repository and creating the archive keyring
RUN sh -c "echo 'deb [signed-by=/usr/share/keyrings/datadog-archive-keyring.gpg] https://apt.datadoghq.com/ stable 7' > /etc/apt/sources.list.d/datadog.list"
RUN touch /usr/share/keyrings/datadog-archive-keyring.gpg
RUN chmod a+r /usr/share/keyrings/datadog-archive-keyring.gpg

# Adding the Datadog GPG Key on each ubuntu system
RUN curl https://keys.datadoghq.com/DATADOG_APT_KEY_CURRENT.public | gpg --no-default-keyring --keyring /usr/share/keyrings/datadog-archive-keyring.gpg --import --batch
RUN curl https://keys.datadoghq.com/DATADOG_APT_KEY_382E94DE.public | gpg --no-default-keyring --keyring /usr/share/keyrings/datadog-archive-keyring.gpg --import --batch
RUN curl https://keys.datadoghq.com/DATADOG_APT_KEY_F14F620E.public | gpg --no-default-keyring --keyring /usr/share/keyrings/datadog-archive-keyring.gpg --import --batch

RUN apt-get update -y
RUN apt-get install datadog-agent datadog-signing-keys

RUN sh -c "sed 's/api_key:.*/api_key: <API-KEY>/' /etc/datadog-agent/datadog.yaml.example > /etc/datadog-agent/datadog.yaml"
RUN sh -c "sed -i 's/# site:.*/site: datadoghq.com/' /etc/datadog-agent/datadog.yaml"
RUN sh -c "chown dd-agent:dd-agent /etc/datadog-agent/datadog.yaml && chmod 640 /etc/datadog-agent/datadog.yaml"

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True
# ENV TZ America/Sao_Paulo

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Install production dependencies.
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install newrelic
RUN pip install ddtrace


ENV NEW_RELIC_APP_NAME=petrosa-strategy-screenings-backtesting
ENV DD_SERVICE=petrosa-strategy-screenings-backtesting
ENV NEW_RELIC_DISTRIBUTED_TRACING_ENABLED=true
ENV NEW_RELIC_MONITOR_MODE=true
# ENV NEW_RELIC_LOG_LEVEL=debug
ENV NEW_RELIC_LOG=/tmp/newrelic.log

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
# CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
CMD ["service", "datadog-agent", "start"]
ENTRYPOINT ["ddtrace-run", "python3", "main.py"]

