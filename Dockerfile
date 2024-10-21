ARG PYTHON_VERSION=3.12
ARG ARCH=linux/amd64
FROM --platform=${ARCH} public.ecr.aws/lambda/python:${PYTHON_VERSION}
WORKDIR ${LAMBDA_TASK_ROOT}
SHELL [ "/bin/bash", "-euxvc"]

ENV PATH="${PATH}:/root/.local/bin:" \
    TZ=Asia/Seoul \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONIOENCODING=UTF-8 \
    PYTHONUNBUFFERED=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Setup timezone, user, and install dependencies, and clean up
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy only the dependencies files to cache them in docker layer
COPY pyproject.toml poetry.lock ${LAMBDA_TASK_ROOT}

RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
    microdnf install gcc -y \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && poetry config virtualenvs.create false  \
    && poetry config installer.max-workers 10 \
    && poetry install --only main --no-interaction --no-ansi --no-root

ARG GIT_HASH
ENV DEPLOYMENT_GIT_HASH=$GIT_HASH

# Make docker to always copy app directory so that source code can be refreshed.
ARG IMAGE_BUILD_DATETIME=unknown
ENV DEPLOYMENT_IMAGE_BUILD_DATETIME=$IMAGE_BUILD_DATETIME

# Copy main app
COPY ./chalice-build/deployment/ ${LAMBDA_TASK_ROOT}/

# The reason for using nobody user is to avoid running the app as root, which can be a security risk.
CMD [ "app.app" ]
