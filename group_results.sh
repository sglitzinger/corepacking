#!/bin/bash
# Groups results from the examined packing techniques
# To be executed in results directory

python ../resultsgrouper.py ./solutions_rectpack_skyline_rot.csv ./solutions_rectpack_skyline_norot.csv
mv solutions_grouped.csv solutions_rectpack_skyline_grouped.csv
python ../resultsgrouper.py ./solutions_rectpack_guillotine_rot.csv ./solutions_rectpack_guillotine_norot.csv 
mv solutions_grouped.csv solutions_rectpack_guillotine_grouped.csv
python ../resultsgrouper.py ./solutions_rectpack_maxrects_rot.csv ./solutions_rectpack_maxrects_norot.csv 
mv solutions_grouped.csv solutions_rectpack_maxrects_grouped.csv
python ../resultsgrouper.py ./solutions_heuristic_random.csv ./solutions_heuristic_corearea.csv ./solutions_heuristic_totalarea.csv 
mv solutions_grouped.csv solutions_heuristic_grouped.csv
