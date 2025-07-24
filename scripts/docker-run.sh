#!/bin/bash
# Docker wrapper script for Knowledge Base Processor
# Makes it easy to run the tool with proper volume mounts and environment variables

set -e

# Default values
IMAGE_TAG="knowledgebase-processor:latest"
WORK_DIR="${PWD}"
CONFIG_FILE=""
COMMAND=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 [OPTIONS] [COMMAND]"
    echo ""
    echo "Options:"
    echo "  -w, --work-dir PATH    Working directory to mount (default: current directory)"
    echo "  -c, --config PATH      Config file path (will be mounted)"
    echo "  -i, --image TAG        Docker image tag (default: knowledgebase-processor:latest)"
    echo "  -h, --help             Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 --help                                    # Show KB help"
    echo "  $0 init                                      # Initialize in current directory"
    echo "  $0 -w ~/Documents init                       # Initialize in ~/Documents"
    echo "  $0 -c ./my-config.json scan                  # Use custom config"
    echo "  $0 publish --watch                           # Watch mode with current directory"
    echo "  $0 -w /data search \"todo\"                   # Search in /data directory"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -w|--work-dir)
            WORK_DIR="$2"
            shift 2
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -i|--image)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -h|--help)
            if [[ -z "$COMMAND" ]]; then
                usage
                exit 0
            else
                COMMAND="$COMMAND $1"
                shift
            fi
            ;;
        *)
            COMMAND="$COMMAND $1"
            shift
            ;;
    esac
done

# Resolve paths
WORK_DIR=$(realpath "$WORK_DIR")

# Build docker run command
DOCKER_CMD="docker run --rm -it --network host"

# Volume mounts
DOCKER_CMD="$DOCKER_CMD -v \"$WORK_DIR:/workspace\""

# Environment variables
DOCKER_CMD="$DOCKER_CMD -e KBP_WORK_DIR=/workspace"
DOCKER_CMD="$DOCKER_CMD -e KBP_HOME=/workspace/.kbp"
DOCKER_CMD="$DOCKER_CMD -e KBP_KNOWLEDGE_BASE_PATH=/workspace"
DOCKER_CMD="$DOCKER_CMD -e KBP_METADATA_STORE_PATH=/workspace/.kbp/metadata"

# Config file handling
if [[ -n "$CONFIG_FILE" ]]; then
    if [[ ! -f "$CONFIG_FILE" ]]; then
        echo -e "${RED}Error: Config file '$CONFIG_FILE' not found${NC}" >&2
        exit 1
    fi
    CONFIG_FILE=$(realpath "$CONFIG_FILE")
    DOCKER_CMD="$DOCKER_CMD -v \"$CONFIG_FILE:/workspace/kbp_config.json\""
    DOCKER_CMD="$DOCKER_CMD -e KBP_CONFIG_PATH=/workspace/kbp_config.json"
fi

# Working directory
DOCKER_CMD="$DOCKER_CMD -w /workspace"

# Image and command
DOCKER_CMD="$DOCKER_CMD $IMAGE_TAG"
if [[ -n "$COMMAND" ]]; then
    DOCKER_CMD="$DOCKER_CMD kb$COMMAND"
else
    DOCKER_CMD="$DOCKER_CMD kb --help"
fi

# Print what we're running (if verbose)
if [[ "${VERBOSE:-}" == "1" ]]; then
    echo -e "${YELLOW}Running: $DOCKER_CMD${NC}" >&2
fi

# Execute
eval $DOCKER_CMD