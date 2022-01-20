'''
Computes max. configurations for chip design via rectangle packing problem solver.
'''


import rectpack
import time
import sys
import os


CHIPWIDTH = None # 2400 # 3200
CHIPHEIGHT = None # 2400 # 3200
ROTATION_ALLOWED = None # False
CORE_ORDER = ["big", "A72", "Mali", "LITTLE"]
PACKING_ALGORITHM = None # rectpack.MaxRectsBssf # rectpack.GuillotineBssfSas # rectpack.SkylineBl


class Core:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.maxrows = int(CHIPHEIGHT // height)
        self.maxcols = int(CHIPWIDTH // width)


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


def main():
    output_file = sys.argv[1]
    alg = sys.argv[2]
    global PACKING_ALGORITHM
    if alg == "maxrectsrot":
        PACKING_ALGORITHM = rectpack.MaxRectsBssf
        ROTATION_ALLOWED = True
    elif alg == "maxrectsnorot":
        PACKING_ALGORITHM = rectpack.MaxRectsBssf
        ROTATION_ALLOWED = False
    elif alg == "guillotinerot":
        PACKING_ALGORITHM = rectpack.GuillotineBssfSas
        ROTATION_ALLOWED = True
    elif alg == "guillotinenorot":
        PACKING_ALGORITHM = rectpack.GuillotineBssfSas
        ROTATION_ALLOWED = False
    elif alg == "skylinerot":
        PACKING_ALGORITHM = rectpack.SkylineBl
        ROTATION_ALLOWED = True
    elif alg == "skylinenorot":
        PACKING_ALGORITHM = rectpack.SkylineBl
        ROTATION_ALLOWED = False
    else:
        print("Packing algorithm unknown! Exiting...")
        sys.exit(1)
    global CHIPWIDTH
    CHIPWIDTH = int(sys.argv[3]) * 100
    global CHIPHEIGHT
    CHIPHEIGHT = int(sys.argv[4]) * 100
    set_coreinfo()
    if len(sys.argv) >= 6:
        input_file = sys.argv[5]
        corecounts, fillwith, placement_order = read_input(input_file)
        rectid = 0
        rectangles = []
        rectangle_types = {}
        for core in placement_order:
            for _ in range(corecounts[core]):
                rectangles.append((COREINFO[core].width, COREINFO[core].height, rectid))
                rectangle_types[rectid] = core
                rectid += 1
        for _ in range(COREINFO[fillwith].maxrows*COREINFO[fillwith].maxcols):
            rectangles.append((COREINFO[fillwith].width, COREINFO[fillwith].height, rectid))
            rectangle_types[rectid] = fillwith
            rectid += 1
        bins = [(CHIPWIDTH,CHIPHEIGHT)]
        packer = rectpack.newPacker(mode=rectpack.PackingMode.Offline, pack_algo=PACKING_ALGORITHM, sort_algo=rectpack.SORT_NONE, rotation=ROTATION_ALLOWED)

        # Add the rectangles to packing queue
        for r in rectangles:
            packer.add_rect(*r)
        # Add the bins where the rectangles will be placed
        for b in bins:
            packer.add_bin(*b)
        # Start packing
        packer.pack()
        # Count cores
        numcts = [0] * 4

        all_rects = packer.rect_list()
        # Print chip design to file, to be processed by plotter
        with open(sys.argv[2], 'w') as cff:
            for rect in all_rects:
                b, x, y, w, h, rid = rect
                cff.write("{},{},{},{},{}\n".format(x, y, w, h, rectangle_types[rid]))
    elif len(sys.argv) == 5:
        # Explore search space
        maxct0 = COREINFO[CORE_ORDER[0]].maxrows * COREINFO[CORE_ORDER[0]].maxcols
        maxct1 = COREINFO[CORE_ORDER[1]].maxrows * COREINFO[CORE_ORDER[1]].maxcols
        maxct2 = COREINFO[CORE_ORDER[2]].maxrows * COREINFO[CORE_ORDER[2]].maxcols

        for i in range(maxct0+1):
            for j in range(maxct1+1):
                for k in range(maxct2+1):
                    # Construct rectangle queue
                    #print("Investigating core counts ({},{},{}), max. ({},{},{})".format(i,j,k,maxct0,maxct1,maxct2))
                    rectid = 0
                    rectangles = []
                    rectangle_types = {}
                    for l in range(len(CORE_ORDER)):
                        core = CORE_ORDER[l]
                        if l == 0:
                            numrects = i
                        elif l == 1:
                            numrects = j
                        elif l == 2:
                            numrects = k
                        elif l == 3:
                            numrects = COREINFO[core].maxrows * COREINFO[core].maxcols
                        for _ in range(numrects):
                            rectangles.append((COREINFO[core].width, COREINFO[core].height, rectid))
                            rectangle_types[rectid] = core
                            rectid += 1
                    bins = [(CHIPWIDTH,CHIPHEIGHT)]

                    packer = rectpack.newPacker(mode=rectpack.PackingMode.Offline, pack_algo=PACKING_ALGORITHM, sort_algo=rectpack.SORT_NONE, rotation=ROTATION_ALLOWED)

                    # Add the rectangles to packing queue
                    for r in rectangles:
                        packer.add_rect(*r)

                    # Add the bins where the rectangles will be placed
                    for b in bins:
                        packer.add_bin(*b)

                    # Start packing
                    packer.pack()

                    # Count cores
                    numcts = [0] * 4

                    all_rects = packer.rect_list()
                    for rect in all_rects:
                        b, x, y, w, h, rid = rect
                        ct = rectangle_types[rid]
                        ctid = CORE_ORDER.index(ct)
                        numcts[ctid] += 1
                        #print(b, x, y, w, h, rid)

                    #print("Core counts placed: {} {} {} {}".format(*numcts))
                    if numcts[0] == i and numcts[1] == j and numcts[2] == k:
                        # Solution is feasible, save number of cores of fourth type added to chip
                        numct3 = numcts[3]
                        # Save layout information to file
                        if not os.path.isdir("/tmp/layouts_rectpack_{}".format(alg)):
                            os.mkdir("/tmp/layouts_rectpack_{}".format(alg))
                        with open("/tmp/layouts_rectpack_{}/layout_{}_{}_{}.csv".format(alg, i, j, k), 'w') as cff:
                            for rect in all_rects:
                                b, x, y, w, h, rid = rect
                                cff.write("{},{},{},{},{}\n".format(x, y, w, h, rectangle_types[rid]))
                    else:
                        numct3 = -1
                    with open(output_file, "a") as srf:
                        srf.write("{},{},{},{}\n".format(i,j,k,numct3))
    else:
        print("Please specify input/output file(s)!")
        sys.exit(1)


if __name__ == "__main__":
    start_time = time.process_time()
    main()
    end_time = time.process_time()
    with open("./timerectpack.log", 'a+') as tlog:
        tlog.write(str(end_time - start_time) + "," + sys.argv[3] + "x" + sys.argv[4] + "," + sys.argv[2] + "\n")
