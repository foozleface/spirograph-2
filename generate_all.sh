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
#   --jobs N       Run N parallel jobs (default: number of CPU cores)
#   --examples     Only process files in examples/ directory
#   --verbose      Show full output from main.py
#   --dry-run      Show what would be generated without running
#

# Don't exit on error - we want to continue processing
set +e

# Default options
PNG_WIDTH=800
OUTPUT_DIR="./output"
SVG_ONLY=false
PNG_ONLY=false
CLEAN=false
DRY_RUN=false
# Default to number of CPU cores
if [[ -f /proc/cpuinfo ]]; then
    JOBS=$(grep -c ^processor /proc/cpuinfo)
elif command -v sysctl &> /dev/null; then
    JOBS=$(sysctl -n hw.ncpu 2>/dev/null || echo 4)
else
    JOBS=4
fi
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
        --jobs|-j)
            JOBS="$2"
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
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            sed -n '2,16p' "$0"
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
mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR="$(cd "$OUTPUT_DIR" && pwd)"

# Find all .ini files recursively (portable - no mapfile)
INI_FILES=()
if [[ "$EXAMPLES_ONLY" == "true" ]]; then
    while IFS= read -r -d '' file; do
        INI_FILES+=("$file")
    done < <(find examples -name "*.ini" -type f -print0 2>/dev/null | sort -z)
else
    while IFS= read -r -d '' file; do
        INI_FILES+=("$file")
    done < <(find . -name "*.ini" -type f ! -path "./.venv/*" ! -path "./output/*" -print0 2>/dev/null | sort -z)
fi

TOTAL=${#INI_FILES[@]}
echo "Found $TOTAL .ini files to process"
echo "Output directory: $OUTPUT_DIR"
echo "Parallel jobs: $JOBS"
echo ""

# Dry run mode
if [[ "$DRY_RUN" == "true" ]]; then
    echo "Dry run - would generate:"
    for ini_file in "${INI_FILES[@]}"; do
        base_name=$(basename "$ini_file" .ini)
        rel_dir=$(dirname "$ini_file")
        rel_dir=${rel_dir#./}
        svg_file="$OUTPUT_DIR/$rel_dir/${base_name}.svg"
        png_file="$OUTPUT_DIR/$rel_dir/${base_name}.png"
        if [[ "$PNG_ONLY" != "true" ]]; then
            echo "  $svg_file"
        fi
        if [[ "$SVG_ONLY" != "true" ]]; then
            echo "  $png_file"
        fi
    done
    exit 0
fi

# Temporary directory for job results
RESULTS_DIR=$(mktemp -d)
trap "rm -rf $RESULTS_DIR" EXIT

# Process a single INI file
process_one() {
    local ini_file="$1"
    local output_dir="$2"
    local png_width="$3"
    local svg_only="$4"
    local png_only="$5"
    local verbose="$6"
    local result_file="$7"

    # Get base name (without path and extension)
    local base_name=$(basename "$ini_file" .ini)

    # Create subdirectory structure mirroring source tree
    local rel_dir=$(dirname "$ini_file")
    rel_dir=${rel_dir#./}
    local sub_dir="$output_dir/$rel_dir"
    mkdir -p "$sub_dir"

    local svg_file="$sub_dir/${base_name}.svg"
    local png_file="$sub_dir/${base_name}.png"

    # Build command
    local cmd="python3 main.py --no-preview"

    if [[ "$png_only" != "true" ]]; then
        cmd="$cmd --svg '$svg_file'"
    fi

    if [[ "$svg_only" != "true" ]]; then
        cmd="$cmd --png '$png_file' --png-width $png_width"
    fi

    cmd="$cmd '$ini_file'"

    # Execute and capture output
    local output
    local result
    if [[ "$verbose" == "true" ]]; then
        echo "[START] $ini_file"
        eval $cmd
        result=$?
        echo "[DONE] $ini_file"
    else
        output=$(eval $cmd 2>&1)
        result=$?
    fi

    # Write result to file
    if [[ $result -eq 0 ]]; then
        echo "OK:$ini_file" >> "$result_file"
    else
        local error_msg=$(echo "$output" | grep -i "error" | head -1)
        echo "FAIL:$ini_file:$error_msg" >> "$result_file"
    fi
}

# Export function for subshells
export -f process_one

# Results file
RESULTS_FILE="$RESULTS_DIR/results.txt"
touch "$RESULTS_FILE"

# Process files in parallel using background jobs
echo "Processing..."
RUNNING=0
IDX=0

for ini_file in "${INI_FILES[@]}"; do
    # Launch job in background
    process_one "$ini_file" "$OUTPUT_DIR" "$PNG_WIDTH" "$SVG_ONLY" "$PNG_ONLY" "$VERBOSE" "$RESULTS_FILE" &

    ((RUNNING++))
    ((IDX++))

    # Wait if we've hit the job limit
    if [[ $RUNNING -ge $JOBS ]]; then
        wait -n 2>/dev/null || wait
        ((RUNNING--))
    fi

    # Progress indicator (every 10 files in non-verbose mode)
    if [[ "$VERBOSE" != "true" ]] && [[ $((IDX % 10)) -eq 0 ]]; then
        echo "  $IDX / $TOTAL ..."
    fi
done

# Wait for remaining jobs
wait

echo ""
echo "================================"

# Count results
COUNT=0
ERRORS=0

while IFS= read -r line; do
    if [[ "$line" == OK:* ]]; then
        ((COUNT++))
        if [[ "$VERBOSE" != "true" ]]; then
            echo "✓ ${line#OK:}"
        fi
    elif [[ "$line" == FAIL:* ]]; then
        ((ERRORS++))
        # Extract filename and error
        rest="${line#FAIL:}"
        fail_file="${rest%%:*}"
        fail_msg="${rest#*:}"
        echo "✗ $fail_file"
        if [[ -n "$fail_msg" ]]; then
            echo "  $fail_msg"
        fi
    fi
done < "$RESULTS_FILE"

echo ""
echo "================================"
echo "Completed: $COUNT files"
if [[ $ERRORS -gt 0 ]]; then
    echo "Errors: $ERRORS files"
fi
echo "Output in: $OUTPUT_DIR"
