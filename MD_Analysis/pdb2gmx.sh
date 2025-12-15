#!/bin/bash

# Default values
INPUT=""
OUTPUT="processed.gro"

# Parse CLI arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -i|--input)
      INPUT="$2"
      shift 2
      ;;
    -o|--output)
      OUTPUT="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 -i input.pdb [-o output.gro]"
      exit 1
      ;;
  esac
done

if [ -z "$INPUT" ]; then
  echo "Error: Input PDB file is required."
  echo "Usage: $0 -i input.pdb [-o output.gro]"
  exit 1
fi

# --- Detect first residue ---
FIRST_RES=$(awk '/^ATOM/ {print $4; exit}' "$INPUT")
if [ "$FIRST_RES" = "MET" ]; then
    NTERM=1   # NH3+ option is 1 for MET-first
else
    NTERM=0   # NH3+ option is 0 otherwise
fi

# --- Detect last residue ---
LAST_RES=$(awk '/^ATOM/ {res=$4} END {print res}' "$INPUT")
if [ "$LAST_RES" = "MET" ]; then
    CTERM=1   # COO- option is 1 for MET-last
else
    CTERM=0   # COO- option is 0 otherwise
fi

echo "Detected first residue: $FIRST_RES (NTERM=$NTERM)"
echo "Detected last residue: $LAST_RES (CTERM=$CTERM)"

# Run pdb2gmx with automatic terminal selection
printf "$NTERM\n$CTERM\n" | gmx pdb2gmx -f "$INPUT" -o "$OUTPUT" -ff charmm36 -water tip3p -ignh -ter


