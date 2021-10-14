'''
Produces a graphical representation of the chip design computed for output of stripcd.py or maxconf4ct.py, i.e. for coordinates and core types as input.
'''


import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches


CHIPWIDTH = 2400
CHIPHEIGHT = 2400
SCALING_FACTOR = 100


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

COLOURS = {
    "big": "red",
    "LITTLE": "green",
    "A72": "orange",
    "Mali": "blue"
}


def plot_chip_design(xs, ys, ws, hs, types, filename):
    fig, ax = plt.subplots(figsize=(CHIPWIDTH/SCALING_FACTOR,CHIPHEIGHT/SCALING_FACTOR))
    plt.axis("scaled")
    fig.canvas.set_window_title('Chip design for configuration ' + filename)
    current_type = types[0]
    switchwh = True
    for i in range(len(xs)):
        colour = COLOURS[types[i]]
        ax.add_patch(
            patches.Rectangle(
                xy=(xs[i], ys[i]),  # point of origin.
                width=ws[i],
                height=hs[i],
                linewidth=1,
                edgecolor='black',
                facecolor=colour,
                fill=True
            )
        )
    ax.set_xlim(0, CHIPWIDTH/SCALING_FACTOR)
    ax.set_ylim(0, CHIPHEIGHT/SCALING_FACTOR)
    #plt.legend(COLOURS, bbox_to_anchor=(1.05, 1.0), loc='upper left', fontsize="large")
    plt.show()


# Argument to be passed: input file name (including path)
def main():
    if len(sys.argv < 2):
        print("Please specify input file (including path)!")
        sys.exit(1)
    else:
        input_file = sys.argv[1]

    chip_df = pd.read_csv(input_file, names=["x", "y", "w", "h", "type"])
    
    xs = chip_df["x"].tolist()
    xs = [x/SCALING_FACTOR for x in xs]
    ys = chip_df["y"].tolist()
    ys = [y/SCALING_FACTOR for y in ys]
    ws = chip_df["w"].tolist()
    ws = [w/SCALING_FACTOR for w in ws]
    hs = chip_df["h"].tolist()
    hs = [h/SCALING_FACTOR for h in hs]
    types = chip_df["type"].tolist()
    print(types)

    plot_chip_design(xs, ys, ws, hs, types, input_file)


if __name__ == "__main__":
    main()
