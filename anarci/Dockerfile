FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
#        git \
        bzip2 \
        ca-certificates \
        libglib2.0-0 \
        libxext6 \
        libsm6 \
        libxrender1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Miniconda
ENV CONDA_VERSION=py39_25.1.1-2
ENV CONDA_DIR=/opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-${CONDA_VERSION}-Linux-x86_64.sh -O /miniconda.sh && \
    bash /miniconda.sh -b -p $CONDA_DIR && \
    rm /miniconda.sh && \
    $CONDA_DIR/bin/conda clean -afy
ENV PATH=$CONDA_DIR/bin:$PATH

# Setup ANARCI
WORKDIR /app

# Copy from local such that we have everything in internal version control
# RUN git clone https://github.com/oxpig/ANARCI.git /app/ANARCI
COPY ./anarci/ANARCI /app/ANARCI
COPY .git/modules/anarci/ANARCI/refs/heads/master /app/ANARCI/ANARCI_VERSION

RUN conda install -c conda-forge biopython -y
RUN conda install -c bioconda hmmer=3.3.2 -y
WORKDIR /app/ANARCI

RUN python setup.py install