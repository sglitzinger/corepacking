# chipdesign
Heuristic for core placement on chip for submission to PDP 2022

# File Overview
- `maxconf.c`: Original heuristic approach for two core types
- `heur4ct.py`: Heuristic approach for up to four core types
- `stripcd.py`: Adaptation of strip packing heuristic in Wei et al. (2017) for chip design problem
- `rectpacker.py`: Computes solutions via the rectpack module
- `resultparser.py`: Provides summaries and histograms
- `cdplotter.py`: Produces visual representations for output of heur4ct.py and stripcd.py
- `cdplotter_maxconf.py`: Produces visual representations for output of maxconf.c
