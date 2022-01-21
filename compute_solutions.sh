#!/bin/bash

CHIPDIMS="32"

for chipdim in $CHIPDIMS
do
    resfolder="/home/sebastian/pvrepos/chipdesign/results_${chipdim}x${chipdim}/"
    mkdir $resfolder

    source activate rectpack
    echo "Computing solutions for rectpack, rotation..."
    python rectpacker.py /tmp/solutions_rectpack_maxrects_rot.csv maxrectsrot $chipdim $chipdim
    echo "Computing solutions for rectpack, no rotation..."
    python rectpacker.py /tmp/solutions_rectpack_maxrects_norot.csv maxrectsnorot $chipdim $chipdim
    echo "Computing solutions for guillotine, rotation..."
    python rectpacker.py /tmp/solutions_rectpack_guillotine_rot.csv guillotinerot $chipdim $chipdim
    echo "Computing solutions for guillotine, no rotation..."
    python rectpacker.py /tmp/solutions_rectpack_guillotine_norot.csv guillotinenorot $chipdim $chipdim
    echo "Computing solutions for skyline, rotation..."
    python rectpacker.py /tmp/solutions_rectpack_skyline_rot.csv skylinerot $chipdim $chipdim
    echo "Computing solutions for skyline, no rotation..."
    python rectpacker.py /tmp/solutions_rectpack_skyline_norot.csv skylinenorot $chipdim $chipdim
    mv /tmp/solutions_rectpack_*.csv $resfolder
    echo "Computing solutions for strip packing..."
    python stripcd.py /tmp/solutions_strippacking.csv $chipdim $chipdim
    mv /tmp/solutions_strippacking.csv $resfolder
    conda deactivate

    source activate shapely
    echo "Computing solutions for heuristic, random..."
    python heur4ct.py /tmp/solutions_heuristic_random.csv random $chipdim $chipdim
    echo "Computing solutions for heuristic, total area..."
    python heur4ct.py /tmp/solutions_heuristic_totalarea.csv totalarea $chipdim $chipdim
    echo "Computing solutions for heuristic, core area..."
    python heur4ct.py /tmp/solutions_heuristic_corearea.csv corearea $chipdim $chipdim
    conda deactivate
    mv /tmp/solutions_heuristic_*.csv $resfolder
done