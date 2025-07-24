#!/bin/bash
# Build script for knowledgebase-processor
# Handles different build approaches including Docker and buildpacks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
BUILD_TYPE="docker"
IMAGE_NAME="knowledgebase-processor"
IMAGE_TAG="latest"
DOCKERFILE="Dockerfile"
BUILDER="paketobuildpacks/builder:full"

# Help function
show_help() {
    echo "Knowledge Base Processor Build Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE        Build type: docker, docker-alpine, buildpack (default: docker)"
    echo "  -n, --name NAME        Image name (default: knowledgebase-processor)"
    echo "  -v, --tag TAG          Image tag (default: latest)"
    echo "  -f, --file FILE        Dockerfile to use (default: Dockerfile)"
    echo "  -b, --builder BUILDER  Buildpack builder (default: paketobuildpacks/builder:full)"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Build with Docker"
    echo "  $0 --type docker-alpine               # Build Alpine variant"
    echo "  $0 --type buildpack                   # Build with Cloud Native Buildpacks"
    echo "  $0 --name myapp --tag v1.0.0          # Custom name and tag"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            BUILD_TYPE="$2"
            shift 2
            ;;
        -n|--name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -v|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -f|--file)
            DOCKERFILE="$2"
            shift 2
            ;;
        -b|--builder)
            BUILDER="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Build functions
build_docker() {
    echo -e "${GREEN}Building with Docker...${NC}"
    echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
    echo "Dockerfile: ${DOCKERFILE}"
    
    docker build \
        -f "${DOCKERFILE}" \
        -t "${IMAGE_NAME}:${IMAGE_TAG}" \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        .
    
    echo -e "${GREEN}Build complete!${NC}"
    echo ""
    echo "To run the image:"
    echo "  docker run --rm ${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    echo "To run with data volume:"
    echo "  docker run --rm -v \$(pwd)/data:/app/data ${IMAGE_NAME}:${IMAGE_TAG} kb scan /app/data"
}

build_docker_alpine() {
    echo -e "${GREEN}Building Alpine variant with Docker...${NC}"
    DOCKERFILE="Dockerfile.alpine"
    build_docker
}

build_buildpack() {
    echo -e "${GREEN}Building with Cloud Native Buildpacks...${NC}"
    echo "Builder: ${BUILDER}"
    echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
    
    # Check if pack is installed
    if ! command -v pack &> /dev/null; then
        echo -e "${RED}Error: 'pack' CLI not found${NC}"
        echo "Please install pack CLI: https://buildpacks.io/docs/tools/pack/"
        exit 1
    fi
    
    # Build with pack
    pack build "${IMAGE_NAME}:${IMAGE_TAG}" \
        --builder "${BUILDER}" \
        --env BP_CPYTHON_VERSION="3.12.*" \
        --env BP_POETRY_VERSION="1.8.*" \
        --path .
    
    echo -e "${GREEN}Build complete!${NC}"
}

# Test the built image
test_image() {
    echo -e "${YELLOW}Testing built image...${NC}"
    
    # Test if kb command works
    if docker run --rm "${IMAGE_NAME}:${IMAGE_TAG}" kb --version; then
        echo -e "${GREEN}✓ Version check passed${NC}"
    else
        echo -e "${RED}✗ Version check failed${NC}"
        exit 1
    fi
    
    # Test help command
    if docker run --rm "${IMAGE_NAME}:${IMAGE_TAG}" kb --help > /dev/null; then
        echo -e "${GREEN}✓ Help command passed${NC}"
    else
        echo -e "${RED}✗ Help command failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}All tests passed!${NC}"
}

# Main execution
echo "Knowledge Base Processor Build Script"
echo "====================================="

case ${BUILD_TYPE} in
    docker)
        build_docker
        test_image
        ;;
    docker-alpine)
        build_docker_alpine
        test_image
        ;;
    buildpack)
        build_buildpack
        test_image
        ;;
    *)
        echo -e "${RED}Unknown build type: ${BUILD_TYPE}${NC}"
        echo "Valid types: docker, docker-alpine, buildpack"
        exit 1
        ;;
esac

# Show image info
echo ""
echo "Image Information:"
echo "=================="
docker images | grep "${IMAGE_NAME}" | grep "${IMAGE_TAG}"

# Show usage examples
echo ""
echo "Usage Examples:"
echo "==============="
echo "# Run CLI"
echo "docker run --rm ${IMAGE_NAME}:${IMAGE_TAG} kb --help"
echo ""
echo "# Process files"
echo "docker run --rm -v \$(pwd)/data:/data ${IMAGE_NAME}:${IMAGE_TAG} kb scan /data"
echo ""
echo "# Run with docker-compose"
echo "docker-compose -f docker-compose.prod.yml up"