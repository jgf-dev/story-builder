#! /bin/bash

# admin user = jeremy.geo@gmail.com

export VDB_HOST_ID=9eea368bfe7f489694d2046019322519
export VDB_API_KEY=3-5I9AP5e0gE5Vaoc7vVYyc4ShtsE2DXTJH56-Uo-aE
export VDB_ENCRYPTION_KEY=mU4xvfHFWLhK40uEkp-8mA
export VDB_TOKEN_SECRET=82b0Uvyjiok2CwQIHEmLo6PYr08VQswGj_LdI4Q9g2wNXO669YOvAQD_mgMTHkGMs_exsBKo_b9RWRN26s8OFA

ARCH=$(uname -m)
OS=$(uname -s)

# Create a directory for persistent data

if [[ "$OS" == "Darwin" ]]; then
    # macOS
    export VDB_DATA_DIR="/Users/Shared/VisualDB"
else
    # Linux
    if [ -d "$HOME/Documents" ]; then
        export VDB_DATA_DIR="$HOME/Documents/VisualDB"
    else
        export VDB_DATA_DIR="$HOME/VisualDB"
    fi
fi
if [ ! -d "$VDB_DATA_DIR" ]; then
    echo "Creating data directory at $VDB_DATA_DIR..."
    mkdir -p "$VDB_DATA_DIR"
    chmod 777 "$VDB_DATA_DIR"
fi

# Choose Docker image based on CPU architecture

if [[ "$ARCH" == "aarch64" ]] || [[ "$ARCH" == "arm64" ]] || [[ "$ARCH" == "armv8"* ]]; then
    export VISUAL_DB_IMAGE="visualdb/visualdb-arm64:latest"
else
    export VISUAL_DB_IMAGE="visualdb/visualdb-x64:latest"
fi

# Pull latest image to ensure we have the most recent version

echo "Pulling Visual DB image: $VISUAL_DB_IMAGE..."
docker pull $VISUAL_DB_IMAGE

# Start container

docker run \
	-d \
	-p 8080:80 \
	-e VDB_HOST_ID \
	-e VDB_API_KEY \
	-e VDB_ENCRYPTION_KEY \
	-e VDB_TOKEN_SECRET \
	-e VDB_DATA_DIR \
	-v "$VDB_DATA_DIR:/data:rw" \
	--restart always \
	--name visualdb \
	$VISUAL_DB_IMAGE

if [ $? -eq 0 ]; then
    echo
    echo Visual DB is running!
    echo Point your browser to http://localhost:8080
fi
