'''
Produces a graphical representation of the chip design computed for output of stripcd.py or maxconf4ct.py, i.e. for coordinates and core types as input.
'''


import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches


CHIPWIDTH = 9.55
CHIPHEIGHT = 9.55


class Core:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.maxrows = int(CHIPHEIGHT // height)
        self.maxcols = int(CHIPWIDTH // width)


COREINFO = {
    "big": Core(5.0, 3.8),
    "LITTLE": Core(2.1, 1.81),
    "C3": Core(3.34,2.54),
    #"C3": Core(2.54,3.34),
    "C4": Core(8.85,6.56)
    #"C4": Core(6.56,8.85)
}

COLOURS = {
    "big": "red",
    "LITTLE": "green",
    "C3": "orange",
    "C4": "blue"
}


def plot_chip_design(xs, ys, types, filename, rot):
    fig, ax = plt.subplots(figsize=(CHIPWIDTH,CHIPHEIGHT))
    fig.canvas.set_window_title('Chip design for configuration ' + filename)
    current_type = types[0]
    switchwh = True
    for i in range(len(xs)):
        if types[i] != current_type:
            switchwh = not switchwh
        current_type = types[i]
        if rot and switchwh:
            w = COREINFO[types[i]].height
            h = COREINFO[types[i]].width
        else:
            w = COREINFO[types[i]].width
            h = COREINFO[types[i]].height
        colour = COLOURS[types[i]]
        ax.add_patch(
            patches.Rectangle(
                xy=(xs[i], ys[i]),  # point of origin.
                width=w,
                height=h,
                linewidth=1,
                edgecolor='black',
                facecolor=colour,
                fill=True
            )
        )
    ax.set_xlim(0, CHIPWIDTH)
    ax.set_ylim(0, CHIPHEIGHT)
    plt.show()


# Argument to be passed: input file name, input type
# Possible input types are:
# - default
# - heur4ct
# For maxconf heuristic with four core types, core rotation must be applied
def main():

    input_file = sys.argv[1]
    input_type = sys.argv[2]

    if input_type == "default":
        rot = False
    elif input_type == "heur4ct":
        rot = True
    else:
        print("Please specify input file name and input type!")
        sys.exit(1)
    chip_df = pd.read_csv(input_file, names=["x", "y", "type"])
    
    xs = chip_df["x"].tolist()
    ys = chip_df["y"].tolist()
    types = chip_df["type"].tolist()
    print(types)

    plot_chip_design(xs, ys, types, input_file, rot)


if __name__ == "__main__":
    main()
