FROM python:3.12

LABEL maintainer="Joris Chau <joris.chau.ext@bayer.com>" app="helix-api"

## environment variables
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG TDP_PYPI

ENV POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \ 
    PATH="/opt/poetry/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    LANG=en_US.UTF-8 \
    TZ=Etc/UTC 

ENV HTTP_PROXY=${HTTP_PROXY}
ENV HTTPS_PROXY=${HTTPS_PROXY}

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get purge -y --auto-remove curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code
COPY pyproject.toml poetry.lock ./
RUN poetry config http-basic.ts-pypi-external "" "${TDP_PYPI}"

# install dependencies
RUN poetry install --no-root 

COPY helix_api/src /code/app

WORKDIR /code/app
EXPOSE 8000

ENTRYPOINT ["poetry", "run", "python3", "-u", "-m", "uvicorn", "main:app", "--host", "0.0.0.0"]
CMD ["--port", "8000"]
