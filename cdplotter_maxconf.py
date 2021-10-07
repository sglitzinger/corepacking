'''
Produces a graphical representation of the chip design for output of maxconf.c, i.e. for configurations as input.
'''


import sys
import matplotlib.pyplot as plt
import matplotlib.patches as patches


CHIPWIDTH = 9.55
CHIPHEIGHT = 9.55
COREWIDTHS = [5.0, 2.1] # big, LITTLE
COREHEIGHTS = [3.8, 1.81]


def plot_chip_design(bigconf, littleconf, lineno):
    fig, ax = plt.subplots(figsize=(CHIPWIDTH,CHIPHEIGHT))
    fig.canvas.set_window_title('Chip design for configuration ' + str(lineno))
    # Plot big cores
    for i in range(len(bigconf)):
        for j in range(bigconf[i]):
            ax.add_patch(
                patches.Rectangle(
                    xy=(j*COREWIDTHS[0], i*COREHEIGHTS[0]),  # point of origin.
                    width=COREWIDTHS[0],
                    height=COREHEIGHTS[0],
                    linewidth=1,
                    edgecolor='black',
                    facecolor='red',
                    fill=True
                )
            )
    # Plot LITTLE cores
    for i in range(len(littleconf)):
        for j in range(littleconf[i]):
            ax.add_patch(
                patches.Rectangle(
                    xy=(CHIPWIDTH-(j+1)*COREWIDTHS[1], CHIPHEIGHT-(i+1)*COREHEIGHTS[1]),  # point of origin.
                    width=COREWIDTHS[1],
                    height=COREHEIGHTS[1],
                    linewidth=1,
                    edgecolor='black',
                    facecolor='green',
                    fill=True
                )
            )
    ax.set_xlim(0, CHIPWIDTH)
    ax.set_ylim(0, CHIPHEIGHT)
    plt.show()


# Arguments to be passed: number of line in configuration file for the configuration to be plotted
def main():
    with open("./configurations_maxconf.csv", 'r') as cf:
        configs = cf.readlines()

    config = configs[int(sys.argv[1])]
    bigconf, littleconf = config.split(",")
    bigconf = bigconf.split(";")
    littleconf = littleconf.split(";")
    bigconf = [int(val) for val in bigconf]
    littleconf = [int(val) for val in littleconf]
    print(bigconf)
    print(littleconf)
    plot_chip_design(bigconf, littleconf, int(sys.argv[1]))


if __name__ == "__main__":
    main()
