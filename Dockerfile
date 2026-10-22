# DESCRIPTION:	  Deploys GooglePhish in Container
# AUTHOR:		  Dhrumil Mistry <contact@dmdhrumilmistry.tech>
# COMMENTS:
#	This file describes how to deploy GooglePhish
#	in a container with all dependencies installed.
# USAGE:
#	# Download googlephish Dockerfile
#	wget [link]
#
#	# Build image
#	docker build -t googlephish .
#
#   # run docker container
#	docker run -d -p 80:8000 googlephish
#

# Use python slim as base image
FROM python:3.12-slim

# Set environment variables
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"
ENV GP_DIR="/GooglePhish"

# Set working directory
WORKDIR $GP_DIR

# Install system dependencies for Poetry and other build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copy project files
COPY . .

# Install project dependencies with Poetry without creating virtualenv (use system python)
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-root

# Check for errors in application
RUN poetry run python manage.py check

# Only generate migration files at build time (no DB write yet)
RUN poetry run python manage.py makemigrations

# Collect static files
RUN poetry run python manage.py collectstatic --noinput

# No credentials are baked into the image.
#
# Upstream shipped an admin password here and printed it in the README,
# so the account guarding every captured credential had a publicly known
# password. There is no admin account now at all: the collector takes one
# password, supplied at run time, and the container will not start
# without it.

# Create data directory so the volume mount point exists
RUN mkdir -p /GooglePhish/data

# Expose port
EXPOSE 8000

# Migrate, create superuser (if needed), then start — runs against the mounted volume DB
CMD ["sh", "-c", "\
    : \"${C2_PASSWORD:?set C2_PASSWORD - see docker-compose.yml}\" && \
    if [ \"${ROLE:-both}\" = c2 ]; then \
        while [ ! -s /GooglePhish/data/db.sqlite3 ]; do sleep 1; done; \
    else \
        poetry run python manage.py migrate; \
    fi && \
    poetry run gunicorn GooglePhish.wsgi:application -b 0.0.0.0:8000 --workers 3 --threads 2 --timeout 60"]
