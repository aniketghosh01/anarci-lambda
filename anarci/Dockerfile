FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

# System deps + dos2unix for CRLF conversion
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget bzip2 ca-certificates dos2unix \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Miniconda
ENV CONDA_VERSION=py39_25.1.1-2
ENV CONDA_DIR=/opt/conda
RUN wget -q https://repo.anaconda.com/miniconda/Miniconda3-${CONDA_VERSION}-Linux-x86_64.sh -O /miniconda.sh && \
    bash /miniconda.sh -b -p $CONDA_DIR && rm /miniconda.sh && \
    $CONDA_DIR/bin/conda clean -afy
ENV PATH=$CONDA_DIR/bin:$PATH

# Setup ANARCI source (ensure submodule content is present in build context)
WORKDIR /app
COPY ./anarci/ANARCI /app/ANARCI

# Normalize CRLF -> LF in ALL pipeline files and ensure RUN_pipeline.sh is executable
RUN find /app/ANARCI/build_pipeline -type f \( -name "*.sh" -o -name "*.py" \) -exec dos2unix {} \; && \
    # Add a bash shebang if missing (forces bash over /bin/sh)
    grep -q '^#!' /app/ANARCI/build_pipeline/RUN_pipeline.sh || \
      sed -i '1s|^|#!/usr/bin/env bash\n|' /app/ANARCI/build_pipeline/RUN_pipeline.sh && \
    chmod +x /app/ANARCI/build_pipeline/RUN_pipeline.sh

# Embed ANARCI version (CI friendly; avoids .git path issues)
ARG ANARCI_VERSION=unknown
RUN echo "$ANARCI_VERSION" > /app/ANARCI/ANARCI_VERSION

# Install runtime deps required by the pipeline (Biopython, HMMER, MUSCLE)
RUN conda install -y -c conda-forge -c bioconda biopython hmmer=3.3.2 muscle && \
    conda clean -afy

# Sanity checks: no CRLF, tools present, script visible
RUN bash -lc "set -e; \
  echo '--- Checking for CRLF remnants ---'; \
  ! grep -R $'\r' /app/ANARCI/build_pipeline && echo 'OK: no CRLF in pipeline files'; \
  echo '--- Tools ---'; \
  which hmmbuild && hmmbuild -h | head -n 2; \
  which hmmpress && hmmpress -h | head -n 2; \
  which muscle && muscle -version | head -n 1; \
  echo '--- Preview RUN_pipeline.sh (first 20 lines) ---'; \
  head -n 20 /app/ANARCI/build_pipeline/RUN_pipeline.sh \
"

# Install ANARCI (this runs RUN_pipeline.sh to build curated alignments, HMMs, germlines.py)
WORKDIR /app/ANARCI


RUN python setup.py install



