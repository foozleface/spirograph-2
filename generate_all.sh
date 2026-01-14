#!/bin/bash
#
# generate_all.sh - Generate PNG and SVG for all .ini files
#
# Usage: ./generate_all.sh [options]
#
# Options:
#   --svg-only     Only generate SVG files
#   --png-only     Only generate PNG files (requires existing SVG)
#   --png-width N  PNG width in pixels (default: 800)
#   --output-dir   Output directory (default: ./output)
#   --clean        Remove output directory before generating
#   --parallel N   Run N processes in parallel (default: 1)
#   --examples     Only process files in examples/ directory
#   --verbose      Show full output from main.py
#

# Don't exit on error - we want to continue processing
set +e

# Default options
PNG_WIDTH=800
OUTPUT_DIR="./output"
SVG_ONLY=false
PNG_ONLY=false
CLEAN=false
PARALLEL=1
EXAMPLES_ONLY=false
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --svg-only)
            SVG_ONLY=true
            shift
            ;;
        --png-only)
            PNG_ONLY=true
            shift
            ;;
        --png-width)
            PNG_WIDTH="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --parallel)
            PARALLEL="$2"
            shift 2
            ;;
        --examples)
            EXAMPLES_ONLY=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            head -20 "$0" | tail -18
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [[ -f ".venv/bin/activate" ]]; then
    source .venv/bin/activate
    echo "Activated virtual environment"
fi

# Clean output directory if requested
if [[ "$CLEAN" == "true" ]] && [[ -d "$OUTPUT_DIR" ]]; then
    echo "Cleaning output directory..."
    rm -rf "$OUTPUT_DIR"
fi

# Create output directory (use absolute path)
OUTPUT_DIR="$(cd "$SCRIPT_DIR" && mkdir -p "$OUTPUT_DIR" && cd "$OUTPUT_DIR" && pwd)"

# Find all .ini files
if [[ "$EXAMPLES_ONLY" == "true" ]]; then
    INI_FILES=$(find examples -name "*.ini" -type f 2>/dev/null | sort)
else
    INI_FILES=$(find . -name "*.ini" -type f ! -path "./.venv/*" ! -path "./output/*" 2>/dev/null | sort)
fi

# Count files
TOTAL=$(echo "$INI_FILES" | grep -c . || echo "0")
echo "Found $TOTAL .ini files to process"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Process files
COUNT=0
ERRORS=0
ERROR_FILES=""

for ini_file in $INI_FILES; do
    # Get base name (without path and extension)
    base_name=$(basename "$ini_file" .ini)
    
    # Create subdirectory structure
    rel_dir=$(dirname "$ini_file")
    rel_dir=${rel_dir#./}
    sub_dir="$OUTPUT_DIR/$rel_dir"
    mkdir -p "$sub_dir"
    
    svg_file="$sub_dir/${base_name}.svg"
    png_file="$sub_dir/${base_name}.png"
    
    # Build command
    cmd="python3 main.py --no-preview"
    
    if [[ "$PNG_ONLY" != "true" ]]; then
        cmd="$cmd --svg '$svg_file'"
    fi
    
    if [[ "$SVG_ONLY" != "true" ]]; then
        cmd="$cmd --png '$png_file' --png-width $PNG_WIDTH"
    fi
    
    cmd="$cmd '$ini_file'"
    
    # Execute and capture output
    if [[ "$VERBOSE" == "true" ]]; then
        echo "Processing: $ini_file"
        echo "Command: $cmd"
        eval $cmd
        result=$?
        echo ""
    else
        # Capture both stdout and stderr
        output=$(eval $cmd 2>&1)
        result=$?
    fi
    
    # Check result
    if [[ $result -ne 0 ]]; then
        echo "✗ $ini_file"
        if [[ "$VERBOSE" != "true" ]]; then
            # Show the error
            echo "  Error: $(echo "$output" | grep -i "error" | head -1)"
        fi
        ((ERRORS++))
        ERROR_FILES="$ERROR_FILES\n  $ini_file"
    else
        echo "✓ $base_name"
        ((COUNT++))
    fi
done

echo ""
echo "================================"
echo "Completed: $COUNT files"
if [[ $ERRORS -gt 0 ]]; then
    echo "Errors: $ERRORS files"
    echo -e "Failed files:$ERROR_FILES"
fi
echo "Output in: $OUTPUT_DIR"
