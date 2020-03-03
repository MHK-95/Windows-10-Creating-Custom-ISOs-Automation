# We are using ubuntu 18.04 since it has a maintained woeusb package.
FROM ubuntu:18.04

# Add the repos for woeusb and python.
RUN apt update && \
    apt install -y software-properties-common && \
    add-apt-repository ppa:nilarimogard/webupd8 && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt update

ARG PYTHON_VERSION=3.8
RUN apt install -y \
    p7zip-full \
    wimtools \
    genisoimage \
    python${PYTHON_VERSION} \
    python3-pip \
    woeusb

# Make symlinks for python
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python${PYTHON_VERSION} 1

# There is a bug in woeusb, https://github.com/slacka/WoeUSB/issues/283.
# Commenting out some lines of /bin/usr/woeusb is a work around since it's not critical.
RUN sed -i -e '\|echo "${VM_DIRTY_BACKGROUND_BYTES}" > /proc/sys/vm/dirty_background_bytes| s/^/#/g' \
    -e '\|echo "${VM_DIRTY_BYTES}" > /proc/sys/vm/dirty_bytes| s/^/#/g' \
    -e '\|echo 0 > /proc/sys/vm/dirty_background_bytes| s/^/#/g' \
    -e '\|echo 0 > /proc/sys/vm/dirty_bytes| s/^/#/g' /usr/bin/woeusb

WORKDIR /work_dir
