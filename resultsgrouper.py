'''
Groups results of provided input files.
'''

import sys
import pandas as pd


res_dfs = []
littlecolnames = []
for i in range(1, len(sys.argv)):
    littlecolname = "LITTLE_" + sys.argv[i]
    littlecolnames.append(littlecolname)
    res_dfs.append(pd.read_csv(sys.argv[i], sep=",", names=["big", "A72", "Mali", littlecolname]))

df = res_dfs[0].copy()
for i in range(1, len(res_dfs)):
    littlecol = res_dfs[i].iloc[:,-1:]
    # ASSUMES IDENTICAL ORDER IN ALL RESULTS FILES!!
    df = pd.concat([df, littlecol], axis=1)

maxlittles = []
for index, row in df.iterrows():
    maxlittles.append(max(row[3:]))
df["maxlittles"] = maxlittles

df.to_csv("./solutions_grouped.csv", columns=["big", "A72", "Mali", "maxlittles"], index=False, header=False)
#print(df)
