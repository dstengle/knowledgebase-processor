#!/bin/bash

# Vocabulary Sync Script
# Synchronizes the local vocabulary cache with the source repository

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VOCAB_DIR="$PROJECT_ROOT/vocabulary"
VERSION_FILE="$VOCAB_DIR/VERSION.json"
VOCAB_FILE="$VOCAB_DIR/kb.ttl"

# Source repository details
SOURCE_REPO="https://github.com/dstengle/knowledgebase-vocabulary"
SOURCE_BRANCH="main"
TEMP_DIR="/tmp/kb-vocab-sync-$$"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_usage() {
    echo "Usage: $0 {check|diff|sync|help}"
    echo ""
    echo "Commands:"
    echo "  check   - Check if local vocabulary is up-to-date"
    echo "  diff    - Show differences between local and remote vocabulary"
    echo "  sync    - Sync vocabulary from source repository"
    echo "  help    - Show this help message"
}

check_dependencies() {
    if ! command -v git &> /dev/null; then
        echo -e "${RED}Error: git is not installed${NC}"
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        echo -e "${RED}Error: curl is not installed${NC}"
        exit 1
    fi
}

get_remote_commit() {
    git ls-remote "$SOURCE_REPO" "refs/heads/$SOURCE_BRANCH" | cut -f1
}

get_local_commit() {
    if [ -f "$VERSION_FILE" ]; then
        python3 -c "import json; print(json.load(open('$VERSION_FILE'))['source_commit'])" 2>/dev/null || echo "unknown"
    else
        echo "unknown"
    fi
}

check_status() {
    echo "Checking vocabulary status..."
    
    local_commit=$(get_local_commit)
    remote_commit=$(get_remote_commit)
    
    echo "Local commit:  $local_commit"
    echo "Remote commit: $remote_commit"
    
    if [ "$local_commit" = "$remote_commit" ]; then
        echo -e "${GREEN}✓ Vocabulary is up-to-date${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Vocabulary needs updating${NC}"
        return 1
    fi
}

show_diff() {
    echo "Fetching remote vocabulary for comparison..."
    
    # Create temp directory
    mkdir -p "$TEMP_DIR"
    cd "$TEMP_DIR"
    
    # Clone repository (shallow clone for efficiency)
    git clone --depth 1 --branch "$SOURCE_BRANCH" "$SOURCE_REPO" repo 2>/dev/null
    
    # Find the vocabulary file in the remote repo
    remote_vocab=""
    if [ -f "repo/vocabulary/kb.ttl" ]; then
        remote_vocab="repo/vocabulary/kb.ttl"
    elif [ -f "repo/kb.ttl" ]; then
        remote_vocab="repo/kb.ttl"
    else
        echo -e "${RED}Error: Could not find kb.ttl in remote repository${NC}"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
    
    # Show diff
    if [ -f "$VOCAB_FILE" ]; then
        echo "Showing differences (local vs remote):"
        echo "======================================="
        diff -u "$VOCAB_FILE" "$remote_vocab" || true
    else
        echo -e "${YELLOW}Local vocabulary file does not exist${NC}"
        echo "Remote vocabulary preview:"
        echo "========================="
        head -n 50 "$remote_vocab"
    fi
    
    # Cleanup
    cd - > /dev/null
    rm -rf "$TEMP_DIR"
}

sync_vocabulary() {
    echo "Syncing vocabulary from source repository..."
    
    # Create vocabulary directory if it doesn't exist
    mkdir -p "$VOCAB_DIR"
    
    # Create temp directory
    mkdir -p "$TEMP_DIR"
    cd "$TEMP_DIR"
    
    # Clone repository
    echo "Cloning repository..."
    git clone --depth 1 --branch "$SOURCE_BRANCH" "$SOURCE_REPO" repo 2>/dev/null
    
    # Get the current commit hash
    cd repo
    current_commit=$(git rev-parse HEAD)
    cd ..
    
    # Find and copy the vocabulary file
    remote_vocab=""
    if [ -f "repo/vocabulary/kb.ttl" ]; then
        remote_vocab="repo/vocabulary/kb.ttl"
    elif [ -f "repo/kb.ttl" ]; then
        remote_vocab="repo/kb.ttl"
    else
        echo -e "${RED}Error: Could not find kb.ttl in remote repository${NC}"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
    
    # Backup existing file if it exists
    if [ -f "$VOCAB_FILE" ]; then
        backup_file="$VOCAB_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        echo "Backing up existing vocabulary to: $backup_file"
        cp "$VOCAB_FILE" "$backup_file"
    fi
    
    # Copy the new vocabulary file
    echo "Copying vocabulary file..."
    cp "$remote_vocab" "$VOCAB_FILE"
    
    # Extract namespace from the vocabulary file
    namespace=$(grep -m1 "@prefix kb:" "$VOCAB_FILE" | sed -n 's/.*<\(.*\)>.*/\1/p' || echo "http://example.org/kb/vocab#")
    
    # Update VERSION.json
    echo "Updating VERSION.json..."
    cat > "$VERSION_FILE" <<EOF
{
  "source_repository": "$SOURCE_REPO",
  "source_commit": "$current_commit",
  "sync_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "namespace": "$namespace",
  "version": "0.1.0-dev",
  "notes": "Synchronized from $SOURCE_REPO at commit $current_commit"
}
EOF
    
    # Cleanup
    cd - > /dev/null
    rm -rf "$TEMP_DIR"
    
    echo -e "${GREEN}✓ Vocabulary synchronized successfully${NC}"
    echo "  Source commit: $current_commit"
    echo "  Namespace: $namespace"
    echo ""
    echo "Next steps:"
    echo "1. Review the changes: git diff vocabulary/"
    echo "2. Run tests: pytest tests/vocabulary/"
    echo "3. Commit changes: git add vocabulary/ && git commit -m 'chore: sync vocabulary from upstream'"
}

# Main script
check_dependencies

case "${1:-help}" in
    check)
        check_status
        ;;
    diff)
        show_diff
        ;;
    sync)
        sync_vocabulary
        ;;
    help|--help|-h)
        print_usage
        ;;
    *)
        echo -e "${RED}Error: Unknown command '$1'${NC}"
        print_usage
        exit 1
        ;;
esac