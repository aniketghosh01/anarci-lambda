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

# Normalize CRLF -> LF in pipeline scripts (fixes $'\r' errors)
RUN find /app/ANARCI/build_pipeline -type f \( -name "*.sh" -o -name "*.py" \) -exec dos2unix {} \;

# COPY .git/modules/anarci/ANARCI/refs/heads/master /app/ANARCI/ANARCI_VERSION
ARG ANARCI_VERSION=unknown
RUN echo "$ANARCI_VERSION" > /app/ANARCI/ANARCI_VERSION

# Install runtime deps (Biopython, HMMER, MUSCLE) required by setup pipeline
RUN conda install -y -c conda-forge -c bioconda biopython hmmer=3.3.2 muscle && \
    conda clean -afy

WORKDIR /app/ANARCI


RUN python setup.py install

