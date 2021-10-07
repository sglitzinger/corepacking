'''
Computes all max. configurations of heterogeneous chip with up to four core types (three currently not supported).
'''


#import time
import sys
from shapely.geometry import Polygon
from shapely.geometry import Point
from shapely import affinity
import matplotlib.pyplot as plt


CHIPWIDTH = 9.55
CHIPHEIGHT = 9.55


class Core:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.maxrows = int(CHIPHEIGHT // height)
        self.maxcols = int(CHIPWIDTH // width)


COREINFO= {
    "big": Core(5.0, 3.8),
    "LITTLE": Core(2.1, 1.81),
    "C3": Core(3.34,2.54),
    "C4": Core(8.85,6.56)
}


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
def fill_chip(polygons, coretype):
    corewidth = COREINFO[coretype].width
    coreheight = COREINFO[coretype].height
    maxrows = COREINFO[coretype].maxrows
    maxcols = COREINFO[coretype].maxcols
    fillconfig = []
    for row in range(maxrows):
        print("row", row)
        numcols = maxcols
        while numcols > 0:
            print("Checking numcols", numcols)
            pg = Polygon([(0.0,row*coreheight), (0.0,(row+1)*coreheight), (numcols*corewidth,(row+1)*coreheight), (numcols*corewidth,row*coreheight)])
            fit = True
            for polg in polygons:
                if pg.intersects(polg):
                    fit = False
            if fit:
                break
            numcols -= 1
        fillconfig.append(numcols)
    return fillconfig


def investigate_design_2ct(corecounts, fillwith):
    coretype = list(corecounts.keys())[0]
    corecount = corecounts[coretype]
    maxcols = COREINFO[coretype].maxcols
    maxrows = COREINFO[coretype].maxrows
    configurations = partitions(corecount, maxcols, maxrows)
    best_config = None
    best_fillconfig = None
    num_fillcores = -1
    for configuration in configurations:
        print(configuration)
        coords = get_polygon_coordinates(configuration, COREINFO[coretype].width, COREINFO[coretype].height)
        polg = Polygon(coords)
        polg = affinity.rotate(polg, 180, (CHIPWIDTH/2,CHIPHEIGHT/2))
        fillconfig = fill_chip([polg], fillwith)
        if sum(fillconfig) > num_fillcores:
            best_config = configuration
            best_fillconfig = fillconfig
            num_fillcores = sum(fillconfig)
        cfdict = {}
        cfdict[coretype] = best_config
        cfdict[fillwith] = best_fillconfig
    return cfdict


def investigate_design_4ct(corecounts, fillwith, placement_order):
    ct0 = placement_order[0]
    cc0 = corecounts[ct0]
    ct1 = placement_order[1]
    cc1 = corecounts[ct1]
    ct2 = placement_order[2]
    cc2 = corecounts[ct2]
    cfsct0 = partitions(cc0, COREINFO[ct0].maxcols, COREINFO[ct0].maxrows)
    cfsct1 = partitions(cc1, COREINFO[ct1].maxcols, COREINFO[ct1].maxrows)
    cfsct2 = partitions(cc2, COREINFO[ct2].maxcols, COREINFO[ct2].maxrows)
    # Keep track of best configurations and number of fill cores
    bc0 = None
    bc1 = None
    bc2 = None
    bcf = None
    num_fc = -1
    for cfct0 in cfsct0:
        # Compute polygon for first core type configuration and rotate clockwise by 90 degrees
        coordsct0 = get_polygon_coordinates(cfct0, COREINFO[ct0].width, COREINFO[ct0].height)
        pgct0 = Polygon(coordsct0)
        pgct0_90 = affinity.rotate(pgct0, -90, (CHIPWIDTH/2,CHIPHEIGHT/2))
        pgct0_180 = affinity.rotate(pgct0, -180, (CHIPWIDTH/2,CHIPHEIGHT/2))
        pgct0_270 = affinity.rotate(pgct0, -270, (CHIPWIDTH/2,CHIPHEIGHT/2))
        for cfct1 in cfsct1:
            coordsct1 = get_polygon_coordinates(cfct1, COREINFO[ct1].width, COREINFO[ct1].height)
            pgct1 = Polygon(coordsct1)
            pgct1_90 = affinity.rotate(pgct1, -90, (CHIPWIDTH/2,CHIPHEIGHT/2))
            pgct1_180 = affinity.rotate(pgct1, -180, (CHIPWIDTH/2,CHIPHEIGHT/2))
            if pgct1.intersects(pgct0_90):
                # If configuration is not feasible, skip
                continue
            for cfct2 in cfsct2:
                coordsct2 = get_polygon_coordinates(cfct2, COREINFO[ct2].width, COREINFO[ct2].height)
                pgct2 = Polygon(coordsct2)
                pgct2_90 = affinity.rotate(pgct2, -90, (CHIPWIDTH/2,CHIPHEIGHT/2))
                if pgct2.intersects(pgct0_180) or pgct2.intersects(pgct1_90):
                    continue
                fillconfig = fill_chip([pgct0_270, pgct1_180, pgct2_90], fillwith)
                if sum(fillconfig) > num_fc:
                    bc0 = cfct0
                    bc1 = cfct1
                    bc2 = cfct2
                    bcf = fillconfig
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


def get_core_coords(configs, placement_order, fillwith):
    coresx = []
    coresy = []
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
    order = placement_order + [fillwith]
    for coretype in order:
        config = configs[coretype]
        for i in range(len(config)):
            for j in range(config[i]):
                x = j*COREINFO[coretype].width
                y = i*COREINFO[coretype].height
                anchor = affinity.rotate(Point(x,y), rot, (CHIPWIDTH/2,CHIPHEIGHT/2))
                # As anchor is always bottom left coordinate, compensate for rotation
                if rot == -270:
                    anchor = Point(anchor.x - COREINFO[coretype].height, anchor.y)
                elif rot == -180:
                    anchor = Point(anchor.x - COREINFO[coretype].width, anchor.y - COREINFO[coretype].height)
                elif rot == -90:
                    anchor = Point(anchor.x, anchor.y - COREINFO[coretype].width)
                coresx.append(anchor.x)
                coresy.append(anchor.y)
                corest.append(coretype)
        rot += rotinc
    return coresx, coresy, corest
    

# Arguments to be passed: input file, output file (including path)
# Example: maxconf4ct.py ./input_maxconf4ct.csv ./configuration_maxconf4ct.csv
# Format for input file:
# - core type to fill chip with
# - core type,cores of core type [in order of placement]
# Example:
# LITTLE
# C3,1
# big,2
# C4,4
def main():
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
    else:
        input_file = "./input.csv"
        output_file = "./configuration_heur4ct.csv"

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

    # corecounts = {}
    # corecounts['big'] = 2
    # corecounts['C4'] = 1
    # corecounts['C3'] = 4
    # placement_order = ['C4', 'big', 'C3']
    configs = investigate_design(corecounts, fillwith, placement_order)
    if len(configs) > 0:
        print("Core counts for best configurations:")
        for key, val in configs.items():
            print("{}: {}, total: {}".format(key, val, sum(val)))
        coresx, coresy, corest = get_core_coords(configs, placement_order, fillwith)
        with open(output_file, 'w') as outf:
            for i in range(len(coresx)):
                outf.write("{},{},{}\n".format(coresx[i], coresy[i], corest[i]))

        # Plot polygons (useful for debugging of get_core_coords fuction and cdplotter.py)
        # placement_order.append('LITTLE')
        # rot = -270
        # for ct in placement_order:
        #     cf = configs[ct]
        #     coords = get_polygon_coordinates(cf, COREINFO[ct].width, COREINFO[ct].height)
        #     print(sum(cf))
        #     print(coords)
        #     pg = Polygon(coords)
        #     pg = affinity.rotate(pg, rot, (CHIPWIDTH/2,CHIPHEIGHT/2))
        #     x,y = pg.exterior.xy
        #     plt.plot(x,y)
        #     rot += 90
        # plt.show()
    else:
        print("No feasible configuration found for given core counts!")


if __name__ == "__main__":
    # start_time = time.process_time()
    main()
    # end_time = time.process_time()
    # with open("timemc4ct.log", 'a+') as tlog:
    #     tlog.write(str(end_time - start_time) + "\n")