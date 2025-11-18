#!/bin/bash
set -e

# Function to handle shutdown
cleanup() {
    echo "Shutting down services..."
    kill $APP_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGTERM SIGINT

# =============================================================================
# DATABASE CONNECTION CHECK FUNCTIONS
# =============================================================================

# Function to check PostgreSQL using pg_isready (proper method)
check_postgres() {
    local max_attempts=10
    local attempt=1
    
    echo "⏳ Checking PostgreSQL connection..."
    
    while [ $attempt -le $max_attempts ]; do
        # Use pg_isready which is the proper way to check PostgreSQL
        if pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB >/dev/null 2>&1; then
            return 0
        fi
        
        echo "⏳ Waiting for PostgreSQL... (attempt $attempt/$max_attempts)"
        sleep 5
        attempt=$((attempt + 1))
    done
    
    return 1
}

# Function to check Redis using redis-cli (proper method)
check_redis() {
    local max_attempts=10
    local attempt=1
    
    echo "⏳ Checking Redis connection..."
    
    while [ $attempt -le $max_attempts ]; do
        # Use redis-cli ping which is the proper way to check Redis
        if redis-cli -h $REDIS_HOST -p $REDIS_PORT ping >/dev/null 2>&1; then
            return 0
        fi
        
        echo "⏳ Waiting for Redis... (attempt $attempt/$max_attempts)"
        sleep 5
        attempt=$((attempt + 1))
    done
    
    return 1
}

# Function to check HTTP endpoint (for Django app)
check_http_service() {
    local url=$1
    local service_name=$2
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s --connect-timeout 5 "$url" >/dev/null 2>&1; then
            return 0
        fi
        echo "⏳ Waiting for $service_name... (attempt $attempt/$max_attempts)"
        sleep 5
        attempt=$((attempt + 1))
    done
    
    return 1
}

# =============================================================================
# DEPENDENCY CHECKS
# =============================================================================

# Check PostgreSQL availability
if ! check_postgres; then
    echo "❌ PostgreSQL not available at $POSTGRES_HOST:$POSTGRES_PORT"
    echo "💡 Check if PostgreSQL container is running and accessible"
    exit 1
fi
echo "✅ PostgreSQL connected successfully at $POSTGRES_HOST:$POSTGRES_PORT"

# Check Redis availability
if ! check_redis; then
    echo "❌ Redis not available at $REDIS_HOST:$REDIS_PORT"
    echo "💡 Check if Redis container is running and accessible"
    exit 1
fi
echo "✅ Redis connected successfully at $REDIS_HOST:$REDIS_PORT"

# =============================================================================
# APPLICATION STARTUP
# =============================================================================

# Start the main FinStor Django application
echo "Starting FinStor application with command: $@"
eval "$@" &
APP_PID=$!
echo "📝 Application started with PID: $APP_PID"

# =============================================================================
# APPLICATION HEALTH CHECK
# =============================================================================

# Verify that the FinStor Django application started successfully
if ! check_http_service "http://localhost:8000" "FinStor"; then
    echo "❌ FinStor application failed to start on port 8000"
    echo "💡 Check Django logs for application startup errors"
    exit 1
fi
echo "✅ FinStor application running successfully on port 8000"

# =============================================================================
# CONTAINER LIFECYCLE MANAGEMENT
# =============================================================================

# Wait for the main application process to complete
wait $APP_PID
cleanup