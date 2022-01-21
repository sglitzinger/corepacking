#!/bin/bash

#ALGORITHMS="rectpack_maxrectsrot rectpack_maxrectsnorot rectpack_guillotinerot rectpack_guillotinenorot rectpack_skylinerot rectpack_skylinenorot strippacking heuristic_random heuristic_totalarea heuristic_corearea"
ALGORITHMS="heuristic_totalarea heuristic_corearea"

for alg in $ALGORITHMS
do
    #python nonproximity.py ./feasible_solution_all_24x24.csv /home/sebastian/Documents/Forschung/squareopt/layouts_24x24/ $alg &
    python nonproximity.py ./feasible_solution_all_32x32.csv /home/sebastian/Documents/Forschung/squareopt/layouts_32x32/ $alg &
done