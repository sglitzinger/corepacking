'''
Parses results files and produces histograms for each input.
'''


import math
import os
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter


CHIPWIDTH = 3200 #2400
CHIPHEIGHT = 3200 #2400


class Core:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.maxrows = int(CHIPHEIGHT // height)
        self.maxcols = int(CHIPWIDTH // width)


COREINFO= {
    "big": Core(500,380),
    "LITTLE": Core(210,181),
    "A72": Core(583,469),
    "Mali": Core(449,394)
}

# Hypothetical square cores
# COREINFO= {
#     "big": Core(436,436),
#     "LITTLE": Core(195,195),
#     "A72": Core(523,523),
#     "Mali": Core(421,421)
# }

TITLES = {
    "solutions_rectpack_maxrects_rot": "rectpack (MaxRects), rotation allowed",
    "solutions_rectpack_maxrects_norot": "rectpack (MaxRects), rotation not allowed",
    "solutions_rectpack_maxrects_grouped": "rectpack (MaxRects)",
    "solutions_rectpack_guillotine_rot": "rectpack (Guillotine), rotation allowed",
    "solutions_rectpack_guillotine_norot": "rectpack (Guillotine), rotation not allowed",
    "solutions_rectpack_guillotine_grouped": "rectpack (Guillotine)",
    "solutions_rectpack_skyline_rot": "rectpack (Skyline), rotation allowed",
    "solutions_rectpack_skyline_norot": "rectpack (Skyline), rotation not allowed",
    "solutions_rectpack_skyline_grouped": "rectpack (Skyline)",
    "solutions_strippacking": "strip packing",
    "solutions_heuristic_random": "corner heuristic, random placement order",
    "solutions_heuristic_totalarea": "corner heuristic, sorted by total area",
    "solutions_heuristic_corearea": "corner heuristic, sorted by core area",
    "solutions_heuristic_grouped": "corner heuristic"
}

INPUT_PATH = "./results_32x32" # "./results_24x24" # "./results_32x32_square" # "./results_24x24_square" 
RESULTS_FILENAME = "./filenames_all.csv" # "./filenames_grouped.csv"

# Areas for chip and all core types
a_big = COREINFO["big"].width * COREINFO["big"].height
a_a72 = COREINFO["A72"].width * COREINFO["A72"].height
a_mali = COREINFO["Mali"].width * COREINFO["Mali"].height
a_little = COREINFO["LITTLE"].width * COREINFO["LITTLE"].height
a_chip = CHIPWIDTH * CHIPHEIGHT

res_dfs = []
with open(RESULTS_FILENAME, "r") as resf:
    filenames = resf.readlines()
filenames = [filename.strip() for filename in filenames]
littlecolnames = []

for filename in filenames:
    littlecolname = "LITTLE_" + os.path.splitext(filename)[0]
    littlecolnames.append(littlecolname)
    df = pd.read_csv(os.path.join(INPUT_PATH, filename), sep=",", names=["big", "A72", "Mali", littlecolname])
    res_dfs.append(df)

# Determine upper bound for number of feasible solutions by chip area constraint
ub_feas = 0
for i in range(COREINFO["big"].maxrows * COREINFO["big"].maxcols + 1):
    for j in range(COREINFO["A72"].maxrows * COREINFO["A72"].maxcols + 1):
        for k in range(COREINFO["Mali"].maxrows * COREINFO["Mali"].maxcols + 1):
            if CHIPWIDTH*CHIPHEIGHT - i*a_big - j*a_a72 - k*a_mali >= 0:
                ub_feas += 1
print("Upper bound for number of feasible solutions:", ub_feas)

df = res_dfs[0].copy()
for i in range(1, len(res_dfs)):
    littlecol = res_dfs[i].iloc[:,-1:]
    # ASSUMES IDENTICAL ORDER IN ALL RESULTS FILES!!
    df = pd.concat([df, littlecol], axis=1)

# Construct query strings to obtain all cases where at least one method yields a feasible solution, and all cases where all methods yield feasible solutions
querystring_exists = ""
querystring_all = ""
for i in range(len(littlecolnames)):
    querystring_exists += littlecolnames[i]
    querystring_all += littlecolnames[i]
    querystring_exists += " != -1"
    querystring_all += " != -1"
    if i != len(littlecolnames)-1:
        querystring_exists += " or "
        querystring_all += " and "

df_feas_exists = df.query(querystring_exists).copy()
#df_feas_exists.to_csv("./feasible_solution_exists.csv", columns=["big", "A72", "Mali"], index=False)
df_feas_all = df.query(querystring_all).copy()
df_feas_all.to_csv("./feasible_solution_all.csv", columns=["big", "A72", "Mali"], index=False)
print("Cases with at least one feasible solution:", len(df_feas_exists))
print("Cases with a feasible solution in all cases:", len(df_feas_all))
print("Number of feasible solutions for...")
for i in range(len(littlecolnames)):
    querystring_exists = littlecolnames[i] + " != -1"
    print("{}: {} ({:4.1f}% of upper bound)".format(TITLES[os.path.splitext(filenames[i])[0]], len(df.query(querystring_exists)), (len(df.query(querystring_exists))/ub_feas)*100))

# Compute upper bounds
LITTLE_ub_exists = []
for index, row in df_feas_exists.iterrows():
    LITTLE_ub_exists.append((a_chip - row["big"] * a_big - row["A72"] * a_a72 - row["Mali"] * a_mali) // a_little)
df_feas_exists["LITTLE_ub"] = LITTLE_ub_exists

LITTLE_ub_all = []
for index, row in df_feas_all.iterrows():
    LITTLE_ub_all.append((a_chip - row["big"] * a_big - row["A72"] * a_a72 - row["Mali"] * a_mali) // a_little)
df_feas_all["LITTLE_ub"] = LITTLE_ub_all

# Compute distances to upper bound
distances_exists = [[] for _ in range(len(littlecolnames))]
for index, row in df_feas_exists.iterrows():
    for i in range(len(littlecolnames)):
        if row[littlecolnames[i]] == -1:
            distances_exists[i].append(-1)
        else:
            distances_exists[i].append(row["LITTLE_ub"] - row[littlecolnames[i]])

distances_all = [[] for _ in range(len(littlecolnames))]
for index, row in df_feas_all.iterrows():
    for i in range(len(littlecolnames)):
        distances_all[i].append(row["LITTLE_ub"] - row[littlecolnames[i]])

# Compute number of exclusive solutions
num_exclusive_solutions = [0] * len(littlecolnames)
for i in range(len(littlecolnames)):
    for j in range(len(distances_exists[i])):
        if distances_exists[i] != -1:
            is_exclusive = True
            for k in range(len(littlecolnames)):
                if k != i and distances_exists[k][j] != -1:
                    is_exclusive = False
                    break
            if is_exclusive:
                num_exclusive_solutions[i] += 1
print("Number of exclusive solutions for...")
for i in range(len(littlecolnames)):
    print("{}: {}".format(TITLES[os.path.splitext(filenames[i])[0]], num_exclusive_solutions[i]))

# Compute maximum and average distances over all cases for each method
maxdists_exists = [max(distancelist) for distancelist in distances_exists]
distances_feas = []
print("Distances from upper bound (at least one feasible solution):")
for i in range(len(filenames)):
    distances_feas.append([distance for distance in distances_exists[i] if distance >= 0])
    print("{}: maximum: {}, average: {:5.2f}".format(os.path.splitext(filenames[i])[0], maxdists_exists[i], sum(distances_feas[i])/len(distances_feas[i])))

maxdists_all = [max(distancelist) for distancelist in distances_all]
print("Distances from upper bound (feasible solution for all methods):")
for i in range(len(filenames)):
    print("{}: maximum: {}, average: {:5.2f}".format(os.path.splitext(filenames[i])[0], maxdists_all[i], sum(distances_all[i])/len(distances_all[i])))

numrows = 1 # len(filenames) # int(math.ceil(len(filenames) / 2))
numcols = len(filenames) # 1 # 2

#fig, axes = plt.subplots(numrows,2,sharex=True,sharey=True,figsize=(5*2,5*numrows))
fig, axes = plt.subplots(numrows,numcols,sharex=True,sharey=True,figsize=(5*numcols,5*numrows))
# for i in range(numrows):
#     for j in range(numcols):
#         if i*numcols+j < len(distances_exists):
#             axes[i][j].hist(distances_exists[i*numcols+j], maxdists_exists[i*numcols+j]+2)
#             axes[i][j].set_title(TITLES[os.path.splitext(filenames[i*numcols+j])[0]])
#             axes[i][j].set_xlabel("distance to upper bound (# LITTLE cores)")
#             axes[i][j].set_ylabel("# configurations")
#             axes[i][j].xaxis.set_tick_params(labelbottom=True)
#             axes[i][j].yaxis.set_tick_params(labelleft=True)
#for i in range(numrows):
for i in range(numcols):
    #axes[i].hist(distances_exists[i], maxdists_exists[i]+2)
    print(maxdists_all[i])
    print(Counter(distances_all[i]))
    axes[i].hist(distances_all[i], len(Counter(distances_all[i])))
    axes[i].set_title(TITLES[os.path.splitext(filenames[i])[0]])
    axes[i].set_xlabel("distance to upper bound (# LITTLE cores)")
    axes[i].set_ylabel("# configurations")
    axes[i].xaxis.set_tick_params(labelbottom=True)
    axes[i].yaxis.set_tick_params(labelleft=True)
plt.subplots_adjust(hspace=0.4)
plt.subplots_adjust(wspace=0.4)
#plt.savefig("./results_hist.png",dpi=300)
plt.savefig("./results_hist.eps",format="eps")
