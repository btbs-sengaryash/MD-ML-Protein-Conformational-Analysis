#!/bin/bash

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <mode> [args...]"
    echo "Modes:"
    echo "  generate_snapshots <interval_ns>"
    echo "  plip"
    exit 1
fi

mode="$1"
shift

generate_snapshots() {
    if [ $# -ne 1 ]; then
        echo "Usage: $0 generate_snapshots <interval_ns>"
        exit 1
    fi
    interval_ns=$1
    # convert ns → ps (multiply by 1000) with decimals allowed using awk
    interval_ps=$(awk "BEGIN {print $interval_ns * 1000}")
    # round to nearest integer since gmx -dt expects integer ps
    interval_ps=$(printf "%.0f" "$interval_ps")

    echo "Generating snapshots every $interval_ns ns ($interval_ps ps)..."

    mkdir -p snapshots
    gmx trjconv -s md_0_10.tpr -f md_0_10.xtc -o snapshots/snap_.pdb -dt $interval_ps -sep -n index.ndx << EOF
Protein_LIG
EOF
}

run_plip() {
    for pdb in snapshots/*.pdb; do
        [ -e "$pdb" ] || continue
        base=$(basename "$pdb" .pdb)
        echo "Processing $pdb -> snapshots/${base}.xml"
        # Remove MODEL/ENDMDL lines before running PLIP
        grep -vE '^(MODEL|ENDMDL)' "$pdb" > "snapshots/${base}_clean.pdb"
        plip -f "snapshots/${base}_clean.pdb" -x
        mv report.xml "snapshots/${base}.xml"
        rm "snapshots/${base}_clean.pdb"
        rm *snap*_clean*.pdb
        # mv *snap*.pdb "snapshots/${base}.pdb"
    done
}

case "$mode" in
    generate_snapshots)
        generate_snapshots "$@"
        ;;
    plip)
        run_plip "$@"
        ;;
    *)
        echo "Unknown mode: $mode"
        exit 1
        ;;
esac

