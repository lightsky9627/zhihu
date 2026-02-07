#!/bin/sh
# Generate random password if not provided
if [ -z "$ADMIN_PASSWORD" ]; then
    # Simple random string generation using tr and urandom
    ADMIN_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 12 | head -n 1)
    export ADMIN_PASSWORD
    echo "========================================"
    echo "GENERATED ADMIN PASSWORD: $ADMIN_PASSWORD"
    echo "========================================"
fi

# Execute the main command
exec "$@"
