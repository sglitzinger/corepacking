'''
Computes all max. configurations of heterogeneous chip with up to four core types (three currently not supported).
'''


import time
import sys
import random
import os
from shapely.geometry import Polygon
from shapely.geometry import Point
from shapely import affinity
from itertools import permutations
import matplotlib.pyplot as plt


CHIPWIDTH = None # 2400 # 3200 #2400
CHIPHEIGHT = None # 2400 # 3200 #2400
CORE_ORDER = ["big", "A72", "Mali", "LITTLE"]


class Core:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.maxrows = int(CHIPHEIGHT // height)
        self.maxcols = int(CHIPWIDTH // width)


class PlacedCore:
    def __init__(self, x, y, w, h, t):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.t = t


COREINFO = None

def set_coreinfo():
    global COREINFO
    COREINFO = {
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


# Cf. https://stackoverflow.com/questions/10035752/elegant-python-code-for-integer-partitioning
def partitions(sum, max_val, max_len):
    """ generator of partitions of sum with limits on values and length """
    # Yields lists in decreasing lexicographical order. 
    # To get any length, omit 3rd arg.
    # To get all partitions, omit 2nd and 3rd args. 

    if sum <= max_val:       # Can start with a singleton.
        yield [sum]

    # Must have first*max_len >= sum; i.e. first >= sum/max_len.
    for first in range(min(sum-1, max_val), max(0, (sum-1)//max_len), -1):
        for p in partitions(sum-first, first, max_len-1):
            yield [first]+p


# Computes the coordinates of the polygon representing a given configuration (i.e. partition), assuming it is placed in the bottom left corner
def get_polygon_coordinates(configuration, corewidth, coreheight):
    if not configuration:
        coords = []
    elif sum(configuration) == 0:
        coords = []
    else:
        coords = [(0.0,0.0)]
        coords.append((0.0,coreheight*len(configuration)))
        coords.append((corewidth*configuration[-1],coreheight*len(configuration)))
        current_height = len(configuration)-1
        while current_height:
            current_height -= 1
            if configuration[current_height] == configuration[current_height+1]:
                continue
            coords.append((coords[-1][0],(current_height+1)*coreheight))
            coords.append((configuration[current_height]*corewidth,(current_height+1)*coreheight))
        coords.append((coords[-1][0],0.0))
    return coords


# Compute configuration for remaining core type which maximizes number of cores placed on chip
# Polygons represent area alredy occupied by cores of different types
# def fill_chip(polygons, coretype):
#     corewidth = COREINFO[coretype].width
#     coreheight = COREINFO[coretype].height
#     maxrows = COREINFO[coretype].maxrows
#     maxcols = COREINFO[coretype].maxcols
#     fillconfig = []
#     for row in range(maxrows):
#         #print("row", row)
#         numcols = maxcols
#         while numcols > 0:
#             #print("Checking numcols", numcols)
#             pg = Polygon([(0.0,row*coreheight), (0.0,(row+1)*coreheight), (numcols*corewidth,(row+1)*coreheight), (numcols*corewidth,row*coreheight)])
#             fit = True
#             for polg in polygons:
#                 if pg.intersects(polg):
#                     fit = False
#             if fit:
#                 break
#             numcols -= 1
#         fillconfig.append(numcols)
#     return fillconfig
# Compute configuration for remaining core type which maximizes number of cores placed on chip
# Polygons represent area alredy occupied by cores of different types
# In constrast to other core types, a list of individual core positions is returned!
def fill_chip(polygons, coretype):
    corewidth = COREINFO[coretype].width
    coreheight = COREINFO[coretype].height
    maxrows = COREINFO[coretype].maxrows
    maxcols = COREINFO[coretype].maxcols
    filllist = []
    for row in range(maxrows):
        #print("row", row)
        col = 0
        hasfit = False
        while col < maxcols:
            pg = Polygon([(col*corewidth,row*coreheight), (col*corewidth,(row+1)*coreheight), ((col+1)*corewidth,(row+1)*coreheight), ((col+1)*corewidth,row*coreheight)])
            fit = True
            for polg in polygons:
                if pg.intersects(polg):
                    fit = False
            if fit:
                hasfit = True
                filllist.append(PlacedCore(col*corewidth, row*coreheight, corewidth, coreheight, coretype))
            else:
                if hasfit:
                    break
            col += 1
    return filllist


def investigate_design_2ct(corecounts, fillwith):
    coretype = list(corecounts.keys())[0]
    corecount = corecounts[coretype]
    maxcols = COREINFO[coretype].maxcols
    maxrows = COREINFO[coretype].maxrows
    configurations = list(partitions(corecount, maxcols, maxrows))
    best_config = None
    best_filllist = None
    num_fillcores = -1
    for configuration in configurations:
        print(configuration)
        coords = get_polygon_coordinates(configuration, COREINFO[coretype].width, COREINFO[coretype].height)
        if coords:
            polg = Polygon(coords)
            polg = affinity.rotate(polg, 180, (CHIPWIDTH/2,CHIPHEIGHT/2))
            polygons = [polg]
        else:
            polygons = []
        filllist = fill_chip(polygons, fillwith)
        if len(filllist) > num_fillcores:
            best_config = configuration
            best_filllist = filllist
            num_fillcores = len(filllist)
        cfdict = {}
        cfdict[coretype] = best_config
        cfdict[fillwith] = best_filllist
    return cfdict


# def investigate_design_4ct(corecounts, fillwith, placement_order):
#     ct0 = placement_order[0]
#     cc0 = corecounts[ct0]
#     ct1 = placement_order[1]
#     cc1 = corecounts[ct1]
#     ct2 = placement_order[2]
#     cc2 = corecounts[ct2]
#     cfsct0 = list(partitions(cc0, COREINFO[ct0].maxcols, COREINFO[ct0].maxrows))
#     cfsct1 = list(partitions(cc1, COREINFO[ct1].maxcols, COREINFO[ct1].maxrows))
#     cfsct2 = list(partitions(cc2, COREINFO[ct2].maxcols, COREINFO[ct2].maxrows))
#     # Keep track of best configurations and number of fill cores
#     bc0 = None
#     bc1 = None
#     bc2 = None
#     bcf = None
#     num_fc = -1
#     for cfct0cforg in cfsct0:
#         print("cf0:", cfct0cforg)
#         if len(cfct0cforg) < COREINFO[ct0].maxrows:
#             to_add = [0] * (COREINFO[ct0].maxrows - len(cfct0cforg))
#             cfct0cf = cfct0cforg + to_add
#         else:
#             cfct0cf = cfct0cforg
#         print("cf0:", cfct0cf)
#         for cfct0 in list(permutations(cfct0cf)):
#             print(cfct0)
#             # Compute polygon for first core type configuration and rotate clockwise by 90 degrees
#             coordsct0 = get_polygon_coordinates(cfct0, COREINFO[ct0].width, COREINFO[ct0].height)
#             if coordsct0:
#                 pgct0 = Polygon(coordsct0)
#                 pgct0_90 = affinity.rotate(pgct0, -90, (CHIPWIDTH/2,CHIPHEIGHT/2))
#                 pgct0_180 = affinity.rotate(pgct0, -180, (CHIPWIDTH/2,CHIPHEIGHT/2))
#                 pgct0_270 = affinity.rotate(pgct0, -270, (CHIPWIDTH/2,CHIPHEIGHT/2))
#                 polygons0 = [pgct0_270]
#             else:
#                 polygons0 = []
#             for cfct1cforg in cfsct1:
#                 #print("cf1:", cfct1cforg)
#                 if len(cfct1cforg) < COREINFO[ct1].maxrows:
#                     to_add = [0] * (COREINFO[ct1].maxrows - len(cfct1cforg))
#                     cfct1cf = cfct1cforg + to_add
#                 else:
#                     cfct1cf = cfct1cforg
#                 #print("cf1:", cfct1cf)
#                 for cfct1 in list(permutations(cfct1cf)):
#                     coordsct1 = get_polygon_coordinates(cfct1, COREINFO[ct1].width, COREINFO[ct1].height)
#                     if coordsct1:
#                         pgct1 = Polygon(coordsct1)
#                         pgct1_90 = affinity.rotate(pgct1, -90, (CHIPWIDTH/2,CHIPHEIGHT/2))
#                         pgct1_180 = affinity.rotate(pgct1, -180, (CHIPWIDTH/2,CHIPHEIGHT/2))
#                         polygons1 = polygons0 + [pgct1_180]
#                         if coordsct0 and pgct1.intersects(pgct0_90):
#                             # If configuration is not feasible, skip
#                             continue
#                     else:
#                         polygons1 = polygons0
#                     for cfct2cforg in cfsct2:
#                         if len(cfct2cforg) < COREINFO[ct2].maxrows:
#                             to_add = [0] * (COREINFO[ct2].maxrows - len(cfct2cforg))
#                             cfct2cf = cfct2cforg + to_add
#                         else:
#                             cfct2cf = cfct2cforg
#                         for cfct2 in list(permutations(cfct2cf)):
#                             coordsct2 = get_polygon_coordinates(cfct2, COREINFO[ct2].width, COREINFO[ct2].height)
#                             if coordsct2:
#                                 pgct2 = Polygon(coordsct2)
#                                 pgct2_90 = affinity.rotate(pgct2, -90, (CHIPWIDTH/2,CHIPHEIGHT/2))
#                                 polygons2 = polygons1 + [pgct2_90]
#                                 if coordsct0 and pgct2.intersects(pgct0_180) or coordsct1 and pgct2.intersects(pgct1_90):
#                                     continue
#                             else:
#                                 polygons2 = polygons1
#                             filllist = fill_chip(polygons2, fillwith)
#                             if len(filllist) > num_fc:
#                                 print("New best config found!")
#                                 bc0 = cfct0
#                                 bc1 = cfct1
#                                 bc2 = cfct2
#                                 bcf = filllist
#                                 num_fc = len(filllist)
#     cfdict = {}
#     if bc0 is not None:
#         # Feasible chip design has been found
#         cfdict[ct0] = bc0
#         cfdict[ct1] = bc1
#         cfdict[ct2] = bc2
#         cfdict[fillwith] = bcf
#     return cfdict


def investigate_design_4ct(corecounts, fillwith, placement_order):
    ct0 = placement_order[0]
    cc0 = corecounts[ct0]
    ct1 = placement_order[1]
    cc1 = corecounts[ct1]
    ct2 = placement_order[2]
    cc2 = corecounts[ct2]
    #print(ct0, cc0)
    #print(ct1, cc1)
    #print(ct2, cc2)
    cfsct0 = list(partitions(cc0, COREINFO[ct0].maxcols, COREINFO[ct0].maxrows))
    cfsct1 = list(partitions(cc1, COREINFO[ct1].maxcols, COREINFO[ct1].maxrows))
    cfsct2 = list(partitions(cc2, COREINFO[ct2].maxcols, COREINFO[ct2].maxrows))
    # Keep track of best configurations and number of fill cores
    bc0 = None
    bc1 = None
    bc2 = None
    bcf = None
    num_fc = -1
    for cfct0 in cfsct0:
        #print("cf0:", cfct0)
        # Compute polygon for first core type configuration and rotate clockwise by 90 degrees
        coordsct0 = get_polygon_coordinates(cfct0, COREINFO[ct0].width, COREINFO[ct0].height)
        if coordsct0:
            #print("Coords for polygon cf0 returned.")
            pgct0 = Polygon(coordsct0)
            pgct0_90 = affinity.rotate(pgct0, -90, (CHIPWIDTH/2,CHIPHEIGHT/2))
            pgct0_180 = affinity.rotate(pgct0, -180, (CHIPWIDTH/2,CHIPHEIGHT/2))
            pgct0_270 = affinity.rotate(pgct0, -270, (CHIPWIDTH/2,CHIPHEIGHT/2))
            polygons0 = [pgct0_270]
        else:
            polygons0 = []
        for cfct1 in cfsct1:
            #print("cf1:", cfct1)
            coordsct1 = get_polygon_coordinates(cfct1, COREINFO[ct1].width, COREINFO[ct1].height)
            if coordsct1:
                #print("Coords for polygon cf1 returned.")
                pgct1 = Polygon(coordsct1)
                pgct1_90 = affinity.rotate(pgct1, -90, (CHIPWIDTH/2,CHIPHEIGHT/2))
                pgct1_180 = affinity.rotate(pgct1, -180, (CHIPWIDTH/2,CHIPHEIGHT/2))
                polygons1 = polygons0 + [pgct1_180]
                #print(pgct0_90)
                #print(pgct1)
                if coordsct0 and pgct1.intersects(pgct0_90):
                    # If configuration is not feasible, skip
                    continue
            else:
                polygons1 = polygons0
            for cfct2 in cfsct2:
                coordsct2 = get_polygon_coordinates(cfct2, COREINFO[ct2].width, COREINFO[ct2].height)
                if coordsct2:
                    pgct2 = Polygon(coordsct2)
                    pgct2_90 = affinity.rotate(pgct2, -90, (CHIPWIDTH/2,CHIPHEIGHT/2))
                    polygons2 = polygons1 + [pgct2_90]
                    if coordsct0 and pgct2.intersects(pgct0_180) or coordsct1 and pgct2.intersects(pgct1_90):
                        continue
                else:
                    polygons2 = polygons1
                filllist = fill_chip(polygons2, fillwith)
                if len(filllist) > num_fc:
                    bc0 = cfct0
                    bc1 = cfct1
                    bc2 = cfct2
                    bcf = filllist
                    num_fc = len(filllist)
    cfdict = {}
    if bc0 is not None:
        # Feasible chip design has been found
        cfdict[ct0] = bc0
        cfdict[ct1] = bc1
        cfdict[ct2] = bc2
        cfdict[fillwith] = bcf
    return cfdict


def investigate_design(corecounts, fillwith, placement_order=None):
    if len(corecounts) == 1:
        # 2 core types
        cfdict = investigate_design_2ct(corecounts, fillwith)
    elif len(corecounts) == 3:
        # 4 core types
        cfdict = investigate_design_4ct(corecounts, fillwith, placement_order)
    else:
        raise ValueError("No implementation present for given number of core types!")
    return cfdict


# Computes coordinates for core types whose numbers are specified beforehand (i.e. all but fill core type)
def get_core_coords(configs, placement_order):
    coresx = []
    coresy = []
    coresw = []
    coresh = []
    corest = []
    if len(configs) == 4:
        # 4 core types
        rot = -270
        rotinc = 90
    elif len(configs) == 2:
        # 2 core types
        rot = -180
        rotinc = 180
    else:
        raise ValueError("Number of core types currently not supported!")
    order = placement_order
    for coretype in order:
        config = configs[coretype]
        for i in range(len(config)):
            for j in range(config[i]):
                w = COREINFO[coretype].width
                h = COREINFO[coretype].height
                # Compensate for rotation w.r.t. to width and height
                x = j*w
                y = i*h
                anchor = affinity.rotate(Point(x,y), rot, (CHIPWIDTH/2,CHIPHEIGHT/2))
                # As anchor is always bottom left coordinate, compensate for rotation
                if rot == -270:
                    anchor = Point(anchor.x - COREINFO[coretype].height, anchor.y)
                elif rot == -180:
                    anchor = Point(anchor.x - COREINFO[coretype].width, anchor.y - COREINFO[coretype].height)
                elif rot == -90:
                    anchor = Point(anchor.x, anchor.y - COREINFO[coretype].width)
                if rot in [-270, -90]:
                    w, h = h, w
                coresx.append(anchor.x)
                coresy.append(anchor.y)
                coresw.append(w)
                coresh.append(h)
                corest.append(coretype)
        rot += rotinc
    return coresx, coresy, coresw, coresh, corest
    

def read_input(input_file):
    corecounts = {}
    placement_order = []
    with open(input_file, 'r') as inpf:
        inputlines = inpf.readlines()
    fillwith = inputlines[0].rstrip("\n")
    for i in range(1, len(inputlines)):
        coretype, corecount = inputlines[i].split(",")
        corecount = int(corecount)
        corecounts[coretype] = corecount
        placement_order.append(coretype)
    return corecounts, fillwith, placement_order


# Possible placement orders:
# - "default": as specified by CORE_ORDER,
# - "random": cores are placed in random order,
# - "totalarea": cores are placed in descending order of core types by total area occupied on chip (i.e., core area x number of cores),
# - "corearea": cores are placed in descending order of core types by area occupied by single core.
def get_placement_order(order, nct0, nct1, nct2):
    if order == "default":
        placement_order = CORE_ORDER[:-1]
    elif order == "random":
        placement_order = CORE_ORDER[:-1].copy()
        random.shuffle(placement_order)
    elif order == "totalarea":
        # Place in order of decreasing area occupied on chip
        coretypes = [CORE_ORDER[0], CORE_ORDER[1], CORE_ORDER[2]]
        areas = []
        areas.append(nct0*COREINFO[CORE_ORDER[0]].width*COREINFO[CORE_ORDER[0]].height)
        areas.append(nct1*COREINFO[CORE_ORDER[1]].width*COREINFO[CORE_ORDER[1]].height)
        areas.append(nct2*COREINFO[CORE_ORDER[2]].width*COREINFO[CORE_ORDER[2]].height)
        coretypes_with_areas = zip(coretypes, areas)
        coretypes_with_areas = sorted(coretypes_with_areas, key=lambda x: x[1], reverse=True)
        placement_order = [coretype for coretype, area in coretypes_with_areas]
    elif order == "corearea":
        # Place in order of decreasing core area
        coretypes = [CORE_ORDER[0], CORE_ORDER[1], CORE_ORDER[2]]
        areas = []
        areas.append(COREINFO[CORE_ORDER[0]].width*COREINFO[CORE_ORDER[0]].height)
        areas.append(COREINFO[CORE_ORDER[1]].width*COREINFO[CORE_ORDER[1]].height)
        areas.append(COREINFO[CORE_ORDER[2]].width*COREINFO[CORE_ORDER[2]].height)
        coretypes_with_areas = zip(coretypes, areas)
        coretypes_with_areas = sorted(coretypes_with_areas, key=lambda x: x[1], reverse=True)
        placement_order = [coretype for coretype, area in coretypes_with_areas]
    else:
        raise ValueError("Placement order unknown!")
    return placement_order

# Arguments to be passed: output file (including path), placement order (i.e. order in which cores are to be placed), input file (optional)
# Example: maxconf4ct.py ./input_maxconf4ct.csv ./configuration_maxconf4ct.csv
# Format for input file:
# - core type to fill chip with
# - core type,#cores of core type
# Example:
# LITTLE
# big,2
# A72,1
# Mali,4
# 
# If no input file is passed, the search space is systematically explored
def main():
    random.seed(1337)
    output_file = sys.argv[1]
    order = sys.argv[2]
    global CHIPWIDTH
    CHIPWIDTH = int(sys.argv[3]) * 100
    global CHIPHEIGHT
    CHIPHEIGHT = int(sys.argv[4]) * 100
    set_coreinfo()
    if len(sys.argv) >= 6:
        input_file = sys.argv[5]
        corecounts, fillwith, placement_order = read_input(input_file)
        placement_order = get_placement_order(order, corecounts[CORE_ORDER[0]], corecounts[CORE_ORDER[1]], corecounts[CORE_ORDER[2]])
        print(placement_order)
        configs = investigate_design(corecounts, fillwith, placement_order)
        if len(configs) > 0:
            #print("Core counts for best configurations:")
            #for key, val in configs.items():
            #    print("{}: {}, total: {}".format(key, val, sum(val)))
            coresx, coresy, coresw, coresh, corest = get_core_coords(configs, placement_order)
            fillcores = configs[fillwith]
            for fillcore in fillcores:
                coresx.append(fillcore.x)
                coresy.append(fillcore.y)
                coresw.append(fillcore.w)
                coresh.append(fillcore.h)
                corest.append(fillcore.t)
            with open(output_file, 'w') as outf:
                for i in range(len(coresx)):
                    outf.write("{},{},{},{},{}\n".format(coresx[i], coresy[i], coresw[i], coresh[i], corest[i]))
        else:
            print("No feasible configuration found for given core counts!")
    elif len(sys.argv) == 5:
        # Explore search space
        maxct0 = COREINFO[CORE_ORDER[0]].maxrows * COREINFO[CORE_ORDER[0]].maxcols
        maxct1 = COREINFO[CORE_ORDER[1]].maxrows * COREINFO[CORE_ORDER[1]].maxcols
        maxct2 = COREINFO[CORE_ORDER[2]].maxrows * COREINFO[CORE_ORDER[2]].maxcols

        for i in range(maxct0+1):
            for j in range(maxct1+1):
                for k in range(maxct2+1):
                    # Construct corelist
                    #print("Investigating core counts ({},{},{}), max. ({},{},{})".format(i,j,k,maxct0,maxct1,maxct2))
                    corecounts = {}
                    for l in range(len(CORE_ORDER)-1):
                        core = CORE_ORDER[l]
                        if l == 0:
                            numcores = i
                        elif l == 1:
                            numcores = j
                        elif l == 2:
                            numcores = k
                        corecounts[core] = numcores
                    fillwith = CORE_ORDER[-1]

                    # Retrieve placement order
                    placement_order = get_placement_order(order, i, j, k)

                    best_configs = investigate_design(corecounts, fillwith, placement_order)
                    if best_configs:
                        # Feasible solution available
                        numct3 = len(best_configs[CORE_ORDER[-1]])
                        coresx, coresy, coresw, coresh, corest = get_core_coords(best_configs, placement_order)
                        fillcores = best_configs[fillwith]
                        for fillcore in fillcores:
                            coresx.append(fillcore.x)
                            coresy.append(fillcore.y)
                            coresw.append(fillcore.w)
                            coresh.append(fillcore.h)
                            corest.append(fillcore.t)
                        if not os.path.isdir("/tmp/layouts_heuristic_{}".format(order)):
                            os.mkdir("/tmp/layouts_heuristic_{}".format(order))
                        with open("/tmp/layouts_heuristic_{}/layout_{}_{}_{}.csv".format(order, i, j, k), 'w') as outf:
                            for m in range(len(coresx)):
                                outf.write("{},{},{},{},{}\n".format(coresx[m], coresy[m], coresw[m], coresh[m], corest[m]))
                    else:
                        numct3 = -1
                    with open(output_file, "a") as shf:
                        shf.write("{},{},{},{}\n".format(i,j,k,numct3))
    else:
        print("Please specify input/output file(s)!")
        sys.exit(1)

    # # Plot polygons (useful for debugging of get_core_coords function and cdplotter.py)
    # rot = -270
    # for ct in placement_order:
    #     cf = configs[ct]
    #     coords = get_polygon_coordinates(cf, COREINFO[ct].width, COREINFO[ct].height)
    #     print(sum(cf))
    #     print(coords)
    #     if coords:
    #         pg = Polygon(coords)
    #         pg = affinity.rotate(pg, rot, (CHIPWIDTH/2,CHIPHEIGHT/2))
    #         x,y = pg.exterior.xy
    #         plt.plot(x,y)
    #     rot += 90
    # for core in configs["LITTLE"]:
    #     x = []
    #     y = []
    #     x.append(core.x)
    #     y.append(core.y)
    #     x.append(core.x)
    #     y.append(core.y + core.h)
    #     x.append(core.x + core.w)
    #     y.append(core.y + core.h)
    #     x.append(core.x + core.w)
    #     y.append(core.y)
    #     x.append(core.x)
    #     y.append(core.y)
    #     plt.plot(x,y)
    # plt.show()


if __name__ == "__main__":
    start_time = time.process_time()
    main()
    end_time = time.process_time()
    with open("timemc4ct.log", 'a+') as tlog:
       tlog.write(str(end_time - start_time) + "," + sys.argv[3] + "x" + sys.argv[4] + "," + sys.argv[2] + "\n")
