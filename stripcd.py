'''
Computes max. configurations for chip design via strip packing heuristic as in Wei et al. (2017).
'''


import sys
import os
import time


CHIPWIDTH = None # 2400 # 3200 # 2400
CHIPHEIGHT = None # 2400 # 3200 # 2400
CORE_ORDER = ["big", "A72", "Mali", "LITTLE"]
EQ_THRESHOLD = 0.001


class Core:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.maxrows = int(CHIPHEIGHT // height)
        self.maxcols = int(CHIPWIDTH // width)


class Segment:
    def __init__(self, x, y, w, lh, rh):
        self.x = x
        self.y = y
        self.w = w
        self.lh = lh
        self.rh = rh


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

# Choose leftmost bottom segment
def choose_segment(skyline):
    segind = 0
    segheight = float('inf')
    for i in range(len(skyline)):
        if skyline[i].y < segheight:
            segheight = skyline[i].y
            segind = i
    return segind


def remove_segment(skyline, segind):
    if len(skyline) == 1:
        raise ValueError("Skyline contains only a single segment, cannot remove last remaining segment!")
    segment = skyline[segind]
    if segind == 0:
        # Segment is leftmost segment
        rightseg = skyline[segind+1]
        rightseg.w = rightseg.w + segment.w
        rightseg.lh = float('inf')
        rightseg.x = 0.0
    elif segind == len(skyline) - 1:
        # Segment is rightmost segment
        leftseg = skyline[segind-1]
        leftseg.w = leftseg.w + segment.w
        leftseg.rh = float('inf')
    else:
        # Segment ist somewhere inbetween
        leftseg = skyline[segind-1]
        rightseg = skyline[segind+1]
        if segment.lh < segment.rh:
            # Level on left hand side
            leftseg.w = leftseg.w + segment.w
            leftseg.rh = abs(rightseg.y - leftseg.y)
        else:
            # Level on right hand side
            rightseg.w = rightseg.w + segment.w
            rightseg.lh = abs(leftseg.y - rightseg.y)
            rightseg.x = segment.x
    skyline.pop(segind)


def insert_segment(skyline, index, left, x, y, w):
    #print("Skyline length:", len(skyline))
    #print("Index:", index)
    if left:
        # Insert to the left of current segment
        if index == 0:
            # Insert as first segment
            lh = float('inf')
            rh = abs(skyline[0].y - y)
            skyline[0].lh = rh
            skyline[0].w -= w
            skyline[0].x += w
            inspos = 0
        else:
            lh = abs(skyline[index-1].y - y)
            rh = abs(skyline[index].y - y)
            skyline[index-1].rh = lh
            skyline[index].lh = rh
            skyline[index].w -= w
            skyline[index].x += w
            inspos = index
    else:
        # Insert to the right of current segment
        if index == len(skyline)-1:
            # Insert as last segment
            rh = float('inf')
            lh = abs(skyline[-1].y - y)
            skyline[-1].rh = lh
            skyline[-1].w -= w
            inspos = len(skyline)
        else:
            lh = abs(skyline[index].y - y)
            rh = abs(skyline[index+1].y - y)
            skyline[index+1].lh = rh
            skyline[index].rh = lh
            skyline[index].w -= w
            inspos = index+1
    newseg = Segment(x, y, w, lh, rh)
    skyline.insert(inspos, newseg)
    

def print_skyline(skyline):
    print("Skyline:")
    for segment in skyline:
        print("{} --> {} at height {}, lh: {}, rh:{}".format(segment.x, segment.x+segment.w, segment.y, segment.lh, segment.rh))


def is_equal(val1, val2):
    if abs(val1 - val2) < EQ_THRESHOLD:
        return True
    return False


# Computes how well each core fits a given segment
# Possible fitness values are:
# -1, if core's width is greater than segment's width
# 0-3, depending on whether core's width equals segment's width, and core's height equals height of neighbouring segments
def get_fitness_value(segment, coretype):
    lh = segment.lh
    rh = segment.rh
    w = segment.w
    if w < COREINFO[coretype].width:
        # Segment is too small
        fitness_value = -1
    else:
        fitness_value = 0
        if is_equal(lh, COREINFO[coretype].height):
            fitness_value += 1
        if is_equal(rh, COREINFO[coretype].height):
            fitness_value += 1
        if is_equal(w, COREINFO[coretype].width):
            fitness_value += 1
    return fitness_value


def get_fitness_values(segment, corelist):
    fitness_values = [None] * len(corelist)
    for i in range(len(corelist)):
        coretype = corelist[i]
        fitness_values[i] = get_fitness_value(segment, coretype)
    return fitness_values


def place_core(skyline, segind, width, height, coresx, coresy, coresw, coresh):
    segment = skyline[segind]
    #print(segind, segment.lh, segment.rh)
    if width > segment.w:
        # Core does not fit segment
        # Should not happen, as this has been checked beforehand
        #print("Segment to small, removing segment...")
        remove_segment(skyline, segind)
        return 0
    coresw.append(width)
    coresh.append(height)
    if is_equal(width, segment.w):
        # Core fits segment exactly, check for skyline adjustments
        #print("Core fits segment exactly, updating skyline...")
        coresx.append(segment.x)
        coresy.append(segment.y)
        segment.y += height
        if height == segment.rh:
            # Cannibalize segment to the right
            #print("Cannibalize segment to the right")
            segment.w += skyline[segind+1].w
            segment.rh = skyline[segind+1].rh
            skyline.pop(segind+1)
        elif segind < len(skyline)-1:
            # If not rightmost segment, update vertical segments
            segment.rh = abs(skyline[segind+1].y - segment.y)
            skyline[segind+1].lh = segment.rh
        if height == segment.lh:
            # Merge with segment to the left
            #print("Merge with segment to the left")
            skyline[segind-1].w += segment.w
            skyline[segind-1].rh = segment.rh
            skyline.pop(segind)
        elif segind > 0:
            # If not leftmost segment, update vertical segments
            segment.lh = abs(skyline[segind-1].y - segment.y)
            skyline[segind-1].rh = segment.lh
    elif is_equal(height, segment.lh):
        #print("Core fits exactly to the left, updating skyline...")
        # Core fits in exactly at the left hand side
        coresx.append(segment.x)
        coresy.append(segment.y)
        # Update skyline
        segment.x += width
        segment.w -= width
        skyline[segind-1].w += width
    elif is_equal(height, segment.rh):
        # Core fits in exactly at the right hand side
        #print("Core fits exactly to the right, updating skyline...")
        coresx.append(segment.x + segment.w - width)
        coresy.append(segment.y)
        # Update skyline
        segment.w -= width
        skyline[segind+1].x -= width
        skyline[segind+1].w += width
    elif abs(height - segment.lh) <= abs(height - segment.rh):
        #print("Better fit to the left, inserting segment...")
        # Better fit at left hand side of segment
        coresx.append(segment.x)
        coresy.append(segment.y)
        insert_segment(skyline, segind, True, segment.x, segment.y + height, width)
    else:
        # Place at right hand side of segment
        #print("Better fit to the right, inserting segment...")
        coresx.append(segment.x + segment.w - width)
        coresy.append(segment.y)
        insert_segment(skyline, segind, False, segment.x + segment.w - width, segment.y + height, width)
    #print("Core placed at ({},{})".format(coresx[-1], coresy[-1]))
    #print_skyline(skyline)
    return 1


def get_actual_chip_height(skyline):
    actual_height = 0.0
    for segment in skyline:
        if segment.y > actual_height:
            actual_height = segment.y
    return actual_height


def choose_core(segment, corelist):
    fitness_values = get_fitness_values(segment, corelist)
    best_fitness = -2
    best_core_index = None
    for i in range(len(fitness_values)):
        if fitness_values[i] > best_fitness:
            best_fitness = fitness_values[i]
            best_core_index = i
    return best_core_index, best_fitness


# Places cores on chip
# fillwith: core type whose number is maximized after cores of other types have been placed in given number
# fitness_guided: core selection can either be determined by fitness or by list order
def place_cores(skyline, corelist, fillwith, fitness_guided):
    coresx = []
    coresy = []
    coresw = []
    coresh = []
    corest = []
    cores_placed = dict.fromkeys(set(corelist), 0)
    chip_full = False
    while corelist:
        segind = choose_segment(skyline)
        segment = skyline[segind]
        if fitness_guided:
            best_core_index, best_fitness = choose_core(segment, corelist)
        else:
            best_core_index = 0
            best_fitness = get_fitness_value(segment, corelist[0])
        coretype = corelist[best_core_index]
        #print("Best fitness:", best_fitness)
        #print("Attempting to place core of type", coretype)
        if best_fitness < 0:
            # Core's width is greater than segment's width
            #print("Segment to small, removing segment...")
            remove_segment(skyline, segind)
        else:
            core_placed = place_core(skyline, segind, COREINFO[coretype].width, COREINFO[coretype].height, coresx, coresy, coresw, coresh)
            #print("Core placed:", core_placed)
            if core_placed:
                # All good, commit placement
                cores_placed[coretype] += 1
                corest.append(coretype)
                corelist.pop(best_core_index)
            else:
                # Should not happen
                raise ValueError("Core placement return value error! Core submitted for placement could not be placed!")
        # Check for chip area usage
        if get_actual_chip_height(skyline) > CHIPHEIGHT:
            chip_full = True
            break
    if not chip_full:
        # Now fill remaining chip area with cores of specified type
        #print("Filling chip with cores of type", fillwith)
        cores_placed[fillwith] = 0
        while get_actual_chip_height(skyline) <= CHIPHEIGHT:
            #print("Attempting to place core of type", fillwith)
            segind = choose_segment(skyline)
            segment = skyline[segind]
            # Check whether core fits segment
            fitness = get_fitness_value(segment, fillwith)
            if fitness < 0:
                #print("Segment to small, removing segment...")
                remove_segment(skyline, segind)
            else:
                core_placed = place_core(skyline, segind, COREINFO[fillwith].width, COREINFO[fillwith].height, coresx, coresy, coresw, coresh)
                if core_placed:
                    # All good, commit placement
                    cores_placed[fillwith] += 1
                    corest.append(fillwith)
                else:
                    # Should not happen
                    raise ValueError("Core placement return value error! Core submitted for placement could not be placed!")
    #else:
        #print("Chip area depleted by cores specified in list, fill type cannot be placed!")
    # Revert last placement
    coresx.pop()
    coresy.pop()
    coresw.pop()
    coresh.pop()
    lasttype = corest.pop()
    cores_placed[lasttype] -= 1
    return cores_placed, coresx, coresy, coresw, coresh, corest, chip_full


def read_input(input_file):
    corelist = []
    with open(input_file, 'r') as inpf:
        inputlines = inpf.readlines()
    fillwith = inputlines[0].rstrip("\n")
    for i in range(1, len(inputlines)):
        coretype, corecount = inputlines[i].split(",")
        corecount = int(corecount)
        cores_added = [coretype] * corecount
        corelist += cores_added
    return corelist, fillwith


# Optional arguments to be passed: input file, output file (including path)
# Example: maxconf4ct.py ./input_maxconf4ct.csv ./configuration_maxconf4ct.csv
# Format for input file:
# - core type to fill chip with
# - core type,cores of core type [in order of placement]
# Example:
# LITTLE
# C3,1
# big,2
# C4,4
# 
# If no arguments are passed, the search space is systematically explored
def main():
    output_file = sys.argv[1]
    global CHIPWIDTH
    CHIPWIDTH = int(sys.argv[2]) * 100
    global CHIPHEIGHT
    CHIPHEIGHT = int(sys.argv[3]) * 100
    set_coreinfo()
    if len(sys.argv) >= 5:
        input_file = sys.argv[4]
        corelist, fillwith = read_input(input_file)
        # Initialize skyline
        initial_segment = Segment(0.0,0.0,CHIPWIDTH,float('inf'),float('inf'))
        skyline = [initial_segment]
        
        # Commence strip packing heuristic
        cores_placed, coresx, coresy, coresw, coresh, corest, is_infeasible = place_cores(skyline, corelist, fillwith, True)
        print("Total cores placed:")
        for key, val in cores_placed.items():
            print("{}: {}".format(key, val))
        with open(output_file, "w") as cdf:
            for i in range(len(corest)):
                cdf.write("{},{},{},{},{}\n".format(coresx[i], coresy[i], coresw[i], coresh[i], corest[i]))
    elif len(sys.argv) == 4:
        # Explore search space
        maxct0 = COREINFO[CORE_ORDER[0]].maxrows * COREINFO[CORE_ORDER[0]].maxcols
        maxct1 = COREINFO[CORE_ORDER[1]].maxrows * COREINFO[CORE_ORDER[1]].maxcols
        maxct2 = COREINFO[CORE_ORDER[2]].maxrows * COREINFO[CORE_ORDER[2]].maxcols

        for i in range(maxct0+1):
            for j in range(maxct1+1):
                for k in range(maxct2+1):
                    # Construct corelist
                    #print("Investigating core counts ({},{},{}), max. ({},{},{})".format(i,j,k,maxct0,maxct1,maxct2))
                    corelist = []
                    for l in range(len(CORE_ORDER)-1):
                        core = CORE_ORDER[l]
                        if l == 0:
                            numcores = i
                        elif l == 1:
                            numcores = j
                        elif l == 2:
                            numcores = k
                        cores_added = [core] * numcores
                        corelist += cores_added
                    fillwith = CORE_ORDER[-1]
                    # Initialize skyline
                    initial_segment = Segment(0.0,0.0,CHIPWIDTH,float('inf'),float('inf'))
                    skyline = [initial_segment]
                    # Commence strip packing heuristic
                    cores_placed, coresx, coresy, coresw, coresh, corest, is_infeasible = place_cores(skyline, corelist, fillwith, True)
                    if not is_infeasible:
                        numct3 = corest.count(CORE_ORDER[-1])
                        if not os.path.isdir("/tmp/layouts_strippacking"):
                            os.mkdir("/tmp/layouts_strippacking")
                        with open("/tmp/layouts_strippacking/layout_{}_{}_{}.csv".format(i, j, k), "w") as cdf:
                            for m in range(len(corest)):
                                cdf.write("{},{},{},{},{}\n".format(coresx[m], coresy[m], coresw[m], coresh[m], corest[m]))
                    else:
                        numct3 = -1
                    with open("/tmp/solutions_strippacking.csv", "a") as ssf:
                        ssf.write("{},{},{},{}\n".format(i,j,k,numct3))
    else:
        print("Please specify input/output file(s)!")
        sys.exit(1)


if __name__ == "__main__":
    start_time = time.process_time()
    main()
    end_time = time.process_time()
    with open("./timestrippack.log", 'a+') as tlog:
        tlog.write(str(end_time - start_time) + "," + sys.argv[2] + "x" + sys.argv[3] + "\n")
            