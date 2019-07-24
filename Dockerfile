# Docker file for the basic web application.
# Using the latest alpine linux. 

FROM alpine:latest

# copy requirements to the container
COPY requirements.txt /tmp/requirements.txt

# install python and postgresql dependencies
RUN apk update && \
    apk add --update bash gcc libffi-dev musl-dev  postgresql-dev python3 python3-dev && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    pip3 install --no-cache-dir -r /tmp/requirements.txt && \
    rm -rf /.wh /root/.cache /var/cache /tmp/requirements.txt

# change the working directory inside the container to /hello
WORKDIR /hello

# copy the application code into the container
COPY . /hello

# set the FLASK_APP environment variable used by flask migrate
ENV FLASK_APP=app.py

# copy the init script to the container
COPY init.sh /usr/local/bin/

# make the init script executable
RUN  chmod u+x /usr/local/bin/init.sh

# expose the container web service endpoint
EXPOSE 8000

# run the app with a non root user
RUN addgroup -g 1000 -S appgroup && \
    adduser  -u 1000 -S appuser -G appgroup

# allow the non root user to access the folder
RUN chown -R appuser:appgroup /hello

# switch to the non root user
USER appuser

# set the init script as the file to be ran during container startups
ENTRYPOINT ["/usr/local/bin/init.sh"]