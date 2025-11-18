# Use official Python 3.11 slim image as base
FROM python:3.11-slim

# =============================================================================
# SYSTEM DEPENDENCIES INSTALLATION
# =============================================================================

# Install required system dependencies for Python packages and application functionality
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    redis-tools \
    libjpeg-dev \
    zlib1g-dev \
    tzdata \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# =============================================================================
# ENVIRONMENT CONFIGURATION
# =============================================================================

# Set time zone for the container (Libya time)
ENV TZ=Africa/Tripoli

# =============================================================================
# NON-ROOT USER SETUP (Security Hardening)
# =============================================================================

# Create restricted user FIRST to ensure proper ownership of all subsequent files
RUN addgroup --system --gid 1001 micro && \
    adduser --system --uid 1001 --gid 1001 --no-create-home micro

# =============================================================================
# PYTHON ENVIRONMENT VARIABLES
# =============================================================================

# Set Python-related environment variables for optimal container performance
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1

# =============================================================================
# APPLICATION SETUP
# =============================================================================

# Set the working directory for all subsequent commands
WORKDIR /app

# =============================================================================
# DEPENDENCIES INSTALLATION (Layer Caching Optimization)
# =============================================================================

# Copy requirements FIRST to leverage Docker layer caching
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# =============================================================================
# APPLICATION CODE COPY
# =============================================================================

# Copy application files with proper ownership for security
COPY --chown=micro:micro . .

# =============================================================================
# PERMISSIONS AND SECURITY
# =============================================================================

# Set proper permissions on the application directory
RUN chmod 755 /app
RUN chown -R micro:micro /app

# =============================================================================
# SWITCH TO NON-ROOT USER (Security)
# =============================================================================

# Switch to the non-privileged user for all subsequent commands
USER micro

# =============================================================================
# VOLUME DIRECTORY PREPARATION
# =============================================================================

# Create directories that will be mounted as volumes
RUN mkdir -p /app/media /app/staticfiles /app/logs

# =============================================================================
# ENTRYPOINT SETUP
# =============================================================================

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# =============================================================================
# CONTAINER RUNTIME CONFIGURATION
# =============================================================================

# Set the entrypoint script that will run before the CMD
ENTRYPOINT ["/app/entrypoint.sh"]