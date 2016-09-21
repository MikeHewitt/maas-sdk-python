# Dockerfile
#
# Ubuntu 16.04 (Xenial) for MAAS Python Flask SDK
#
# @author      Kealan McCusker <kealan.mccusker@miracl.com>
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# NOTES:
#
# To create the image execute:
#     docker build --tag=miracl/flasksdk .
#
# To run container as deamon:
#     docker run -d -p 5000:5000 miracl/flasksdk
#
# To log into the newly created container:
#     docker run -t -i --entrypoint="/bin/bash" -p 5000:5000 miracl/flasksdk 
#
# To get the container ID:
#     CONTAINER_ID=`docker ps -a | grep miracl/flasksdk | cut -c1-12`
#
# To delete the newly created docker container:
#     docker rm -f $CONTAINER_ID
#
# To delete the docker image:
#     docker rmi -f miracl/flasksdk
#
# ------------------------------------------------------------------------------

FROM ubuntu:xenial
MAINTAINER support@miracl.com

ENV TERM linux
ENV HOME /app

# add repositories and update
RUN apt-get update -y && apt-get -y dist-upgrade && \
    apt-get install -y apt-utils software-properties-common python-software-properties && \
    apt-add-repository universe && \
    apt-add-repository multiverse && \
    apt-get update

# install packages
RUN apt-get install -y cmake git build-essential python-dev python-pip libffi-dev python-setuptools  libssl-dev 

RUN pip install --upgrade pip

# Install SDK
COPY . /app
WORKDIR /app
RUN python setup.py install

# Run service
WORKDIR /app/samples
ENTRYPOINT ["python"]
CMD ["flask_sample.py"]
