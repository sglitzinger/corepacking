'''
Parses results files and produces histograms for each input.
'''


import math
import os
import pandas as pd
import matplotlib.pyplot as plt


CHIPWIDTH = 2400
CHIPHEIGHT = 2400


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

TITLES = {
    "solutions_rectpack_maxrects_rot": "rectpack (MaxRects), rotation allowed",
    "solutions_rectpack_maxrects_norot": "rectpack (MaxRects), rotation not allowed",
    "solutions_rectpack_guillotine_rot": "rectpack (Guillotine), rotation allowed",
    "solutions_rectpack_guillotine_norot": "rectpack (Guillotine), rotation not allowed",
    "solutions_rectpack_skyline_rot": "rectpack (Skyline), rotation allowed",
    "solutions_rectpack_skyline_norot": "rectpack (Skyline), rotation not allowed",
    "solutions_strippacking": "strip packing",
    "solutions_heuristic_random": "corner heuristic, random placement order",
    "solutions_heuristic_totalarea": "corner heuristic, sorted by total area",
    "solutions_heuristic_chiparea": "corner heuristic, sorted by chip area"
}

INPUT_PATH = "./results_24x24/"
RESULTS_FILENAME = "./rectpack_filenames.csv"

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

# Construct query string to obtain all cases where at least one method yields a feasible solution
querystring = ""
for i in range(len(littlecolnames)):
    querystring += littlecolnames[i]
    querystring += " != -1"
    if i != len(littlecolnames)-1:
        querystring += " or "

df_feas = df.query(querystring).copy()
print("Cases with at least one feasible solution:", len(df_feas))
print("Number of feasible solutions for...")
for i in range(len(littlecolnames)):
    querystring = littlecolnames[i] + " != -1"
    print("{}: {} ({:5.2f}% of upper bound)".format(os.path.splitext(filenames[i])[0], len(df.query(querystring)), (len(df.query(querystring))/ub_feas)*100))

# Compute upper bounds
LITTLE_ub = []
for index, row in df_feas.iterrows():
    LITTLE_ub.append((a_chip - row["big"] * a_big - row["A72"] * a_a72 - row["Mali"] * a_mali) // a_little)
df_feas["LITTLE_ub"] = LITTLE_ub

# Compute distances to upper bound
distances = [[] for _ in range(len(littlecolnames))]
for index, row in df_feas.iterrows():
    for i in range(len(littlecolnames)):
        if row[littlecolnames[i]] == -1:
            distances[i].append(-1)
        else:
            distances[i].append(row["LITTLE_ub"] - row[littlecolnames[i]])
        
# Compute maximum and average distances over all cases for each method
maxdists = [max(distancelist) for distancelist in distances]
distances_feas = []
print("Distances from upper bound:")
for i in range(len(filenames)):
    distances_feas.append([distance for distance in distances[i] if distance >= 0])
    print("{}: maximum: {}, average: {:5.2f}".format(os.path.splitext(filenames[i])[0], maxdists[i], sum(distances_feas[i])/len(distances_feas[i])))

numrows = int(math.ceil(len(filenames) / 2))

fig, axes = plt.subplots(numrows,2,sharex=True,sharey=True,figsize=(5*2,5*numrows))
for i in range(numrows):
    for j in range(2):
        if i*2+j < len(distances):
            axes[i][j].hist(distances[i*2+j], maxdists[i*2+j]+2)
            axes[i][j].set_title(TITLES[os.path.splitext(filenames[i*2+j])[0]])
            axes[i][j].set_xlabel("distance to upper bound (# LITTLE cores)")
            axes[i][j].set_ylabel("# cases")
            axes[i][j].xaxis.set_tick_params(labelbottom=True)
            axes[i][j].yaxis.set_tick_params(labelleft=True)
plt.subplots_adjust(hspace=0.4)
plt.subplots_adjust(wspace=0.4)
plt.savefig("./results_hist.png",dpi=300)
