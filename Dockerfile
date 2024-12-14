ARG PYTHON_VERSION=3.12
ARG ARCH=linux/amd64

# ==============================================================================
# Frontend Builder
FROM node:22-alpine AS frontend-builder
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

COPY ./frontend /app
RUN rm -rf /app/node_modules
WORKDIR /app
RUN pnpm fetch
RUN pnpm install -r --offline
RUN pnpm run build

# ==============================================================================
FROM --platform=${ARCH} public.ecr.aws/lambda/python:${PYTHON_VERSION} AS runtime
WORKDIR ${LAMBDA_TASK_ROOT}
SHELL [ "/bin/bash", "-euxvc"]

ENV PATH="${PATH}:/root/.local/bin:" \
    TZ=Asia/Seoul \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONIOENCODING=UTF-8 \
    PYTHONUNBUFFERED=1

# Setup timezone, user, and install dependencies, and clean up
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy only the dependencies files to cache them in docker layer
COPY pyproject.toml poetry.lock ${LAMBDA_TASK_ROOT}

RUN --mount=type=cache,target=/home/.cache/pypoetry \
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
COPY ./runtime/ ${LAMBDA_TASK_ROOT}/

# Copy frontend build
COPY --from=frontend-builder /app/dist ${LAMBDA_TASK_ROOT}/frontend/admin

CMD [ "app.app" ]
