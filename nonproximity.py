'''
Computes nonproximity measure for chip layouts.
'''


import sys
import os
import pandas as pd
import math
from shapely.geometry import Polygon


CORE_ORDER = ["big", "A72", "Mali", "LITTLE"]
NORMALIZE_PAIRWISE_DISTANCE = True


class Core:
    def __init__(self, width, height):
        self.width = width
        self.height = height


COREINFO = {
    "big": Core(500,380),
    "LITTLE": Core(210,181),
    "A72": Core(583,469),
    "Mali": Core(449,394)
}


def compute_normalized_pairwise_dist(x_orig, y_orig, x_dest, y_dest, core_type):
    # Use Manhattan distance
    distance_x = abs(x_orig - x_dest)
    distance_y = abs(y_orig - y_dest)
    if NORMALIZE_PAIRWISE_DISTANCE:
        distance_x /= COREINFO[core_type].width
        distance_y /= COREINFO[core_type].height
    return distance_x + distance_y


def compute_core_centers(df_cores):
    core_centers_x = []
    core_centers_y = []
    for index, row in df_cores.iterrows():
        core_centers_x.append(row['x'] + row['w'] / 2)
        core_centers_y.append(row['y'] + row['h'] / 2)
    return core_centers_x, core_centers_y


def compute_ct_distance(df_layout, core_type):
    #print(df_layout)
    df_cores = df_layout[df_layout["ct"] == core_type]
    core_polygons = []
    for index, row in df_cores.iterrows():
        core_polygons.append(Polygon([(row['x'], row['y']), (row['x'], row['y'] + row['h']), (row['x'] + row['w'], row['y'] + row['h']), (row['x'] + row['w'], row['y'])]))
    mindists = []
    for i in range(len(core_polygons)):
        mindist = float('inf')
        for j in range(len(core_polygons)):
            if j != i:
                pi = core_polygons[i]
                pj = core_polygons[j]
                if pi.intersects(pj) and pi.intersection(pj).geom_type != "Point":
                    # Overlapping should not happen
                    if pi.intersection(pj).geom_type == "Polygon":
                        print("Error! Cores overlapping!")
                    # Intersection is line, therefore minimum distance is 0
                    mindist = 0
                    break
                else:
                    # Cores are not placed next to each other, compute normalized Manhattan distance
                    dist = compute_normalized_pairwise_dist(pi.centroid.x, pi.centroid.y, pj.centroid.x, pj.centroid.y, core_type)
                    if dist < mindist:
                        mindist = dist
        mindists.append(mindist)
    #print("Largest distance {}: {}".format(core_type, largest_pairwise_distance))
    return max(mindists)


# Arguments to be passed: file listing the configurations to be examined (including path)
def main():
    if len(sys.argv) < 4:
        print("Please specify file listing the configurations to be examined, path to layout files, and algorithm")
        sys.exit(1)
    df_configs = pd.read_csv(sys.argv[1])
    layout_path = sys.argv[2]
    alg = sys.argv[3]
    print("Examining results for algorithm", alg)
    #print(df_configs)
    ct_distances_all = {}
    nonproximities = []
    for ct in CORE_ORDER:
        ct_distances_all[ct] = []
    #print(ct_distances_over_lower_bound)
    for index, row in df_configs.iterrows():
        #print("Examining configuration ({},{},{})...".format(row[CORE_ORDER[0]], row[CORE_ORDER[1]], row[CORE_ORDER[2]]))
        df_layout = pd.read_csv(os.path.join(layout_path, "layouts_{}/layout_{}_{}_{}.csv".format(alg, row[CORE_ORDER[0]], row[CORE_ORDER[1]], row[CORE_ORDER[2]])), names=["x", "y", "w", "h", "ct"])
        ct_distances_config = []
        for ct in CORE_ORDER:
            #print(df_layout["ct"].values)
            if len(df_layout[df_layout["ct"] == ct]) > 1:
                # There should be at least 2 cores of given type to meaningfully compute nonproximity
                ct_distance = compute_ct_distance(df_layout, ct)
                ct_distances_all[ct].append(ct_distance)
                ct_distances_config.append(ct_distance)
        #print("Distances for configuration ({},{},{}): {}".format(row[CORE_ORDER[0]], row[CORE_ORDER[1]], row[CORE_ORDER[2]], ct_distances))
        if max(ct_distances_config) < 0:
            print("Negative nonproximity for configuration ({},{},{})!".format(row[CORE_ORDER[0]], row[CORE_ORDER[1]], row[CORE_ORDER[2]]))
        nonproximities.append(sum(ct_distances_config)/len(ct_distances_config))
    #print("Maximum nonproximities over all core types:", nonproximities)
    if not os.path.isfile("./nonproximities.csv"):
        with open("./nonproximities.csv", 'w') as npf:
            npf.write("algorithm,core type,max. nonproximity,min. nonproximity,avg. nonproximity\n")
    maxnp = max(nonproximities)
    minnp = min(nonproximities)
    avgnp = sum(nonproximities)/len(nonproximities)
    print("Maximum nonproximity over all core types and configurations: {} at index {}".format(maxnp, nonproximities.index(maxnp)))
    print("Minimum nonproximity over all core types and configurations: {} at index {}".format(minnp, nonproximities.index(minnp)))
    print("Average nonproximity over all core types and configurations:", avgnp)
    with open("./nonproximities.csv", 'a') as npf:
        npf.write("{},{},{},{},{}\n".format(alg,"all",maxnp,minnp,avgnp))
        for ct in CORE_ORDER:
            distances = ct_distances_all[ct]
            if distances:
                maxnpct = max(distances)
                minnpct = min(distances)
                avgnpct = sum(distances)/len(distances)
                npf.write("{},{},{},{},{}\n".format(alg, ct, maxnpct, minnpct, avgnpct))
                print("Maximum nonproximity over all configurations for core type {}: {} at index {}".format(ct, maxnpct, distances.index(maxnpct)))
                print("Minimum nonproximity over all configurations for core type {}: {} at index {}".format(ct, minnpct, distances.index(minnpct)))
                print("Average nonproximity over all configurations for core type {}: {}".format(ct, avgnpct))
    print("Examination of results for algorithm {} terminated.".format(alg))


if __name__ == "__main__":
    main()
