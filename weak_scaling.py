from collections import defaultdict
import os
import fileinput
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt



class process(object):

    def __init__(self, base_dir=None, dir_list=None, num_funcs=10):
        '''base_dir is the directory where this will be run, it should
        contain the directories in dir_list.
        num_funcs is the number of top functions to track'''
        self.base_dir = base_dir
        self.dir_list = dir_list     #directory list containing runs from a different number of cpus
        self.columns = set()         #columns in dataframe
        self.columns.add('Total')
        self.startlines = {}         #start of tinyprofile exclusive data
        self.endlines = {}           #last part of tinyprofile exclusive data to keep
        self.content = {}            #dict that stores data read in from tinyprofile files
        self.num_rows = 0            #rows in dataframe
        self.num_funcs = 10          #Number of most time consuming functions to track
        nested_dict = lambda: defaultdict(nested_dict)
        self.results = nested_dict() #dictionary to store parsed results in
        self.df = None               #dataframe of results dictionary

    def preprocess(self):
        '''base_dir = direcotry where all the data directories are located
        dir_list = list of directories in base dir to search for data, named after
        the number of processors that were run for that test
        num_funcs = Find top num_func functions to collect data on later
        columns = set of most time consuming functions to colelct data on,
        (could be empty)

        num_rows = number of rows dataframe will need (for preallocating)
        content = dictionary of data read in from files
        startlines = dictonary of lines where function data starts
        endlines = dictionary where function data ends'''

        for ii in self.dir_list:
            directory = self.base_dir + "/" + ii

            # Find top 10 time consuming functions in each file
            # and make dataframe using these results
            for filename in os.listdir(directory):
                if ii in filename:
                    self.num_rows += 1
                    with open(directory + '/' + filename, 'r') as f:

                        self.content[filename] = f.readlines()

                        # Find start and end of exclusive function data in mfix output
                        self.startlines[filename] = 0
                        self.endlines[filename] = 0

                        for jj, line in enumerate(self.content[filename]):
                            self.content[filename][jj] = line.replace(", ", "_")

                            if 'name' in line.lower() and '-----' in self.content[filename][jj + 1]:
                                self.startlines[filename] = jj + 2

                            if '---------' in self.content[filename][jj] and 'incl.' in self.content[filename][jj + 3].lower():
                                self.endlines[filename] = jj - 1
                                break

                        # add function names to set
                        for jj in range(0, self.num_funcs):
                            self.columns.add(self.content[filename][self.startlines[filename] + jj].split()[0])
            #print(self.columns)
        self.columns = sorted(list(self.columns))

    def prefill_dict(self):
        '''results = nested dictionary with lists filled with nan'''
        # Prefill dictionary with nan
        for ii in self.dir_list:
            np = int(ii.split("_")[1])
            directory = self.base_dir + "/" + ii
            for filename in os.listdir(directory):
                if ii in filename:
                    # (date, hash, np) = total, f1...fn
                    date = filename.split("_")[0]
                    short_hash = filename.split("_")[1]
                    self.results[date][short_hash][np] = []

                    # total, all funtions
                    for jj in range(0, len(self.columns)):
                        self.results[date][short_hash][np].append(float('nan'))



    def add_data_to_dict(self):

        for filename, lines in self.content.items():
            fsplit = filename.split("_")
            date = fsplit[0]
            short_hash = fsplit[1]
            np = int(fsplit[3])

            for line_num, line in enumerate(lines):
                if line_num >= self.startlines[filename] and line_num <= self.endlines[filename]:
                    # Loop through functions and get times
                    for kk, func in enumerate(self.columns):
                        if func in line:
                            # kk = func index in list, line.split()[3] = average func time
                            self.results[date][short_hash][np][kk] = float(line.split()[3])
                if 'time spent in main ' in line.lower():
                    index = self.columns.index("Total")
                    self.results[date][short_hash][np][index] = float(line.split()[-1])

    # Dictionary to dataframe
    def dict_to_df(self):
        self.df = pd.DataFrame(index=np.arange(0, self.num_rows), columns=['Date', 'Hash', 'NP']+self.columns)

        ii = 0
        for key1, val1 in self.results.items():
            for key2, val2 in self.results[key1].items():
                for key3, val3 in self.results[key1][key2].items():
                    #print(key1, key2, key3, val3)
                    self.df.loc[ii] = [key1, key2, key3] + val3
                    ii += 1

        #Make unique 'datehash' column
        self.df['DateHash'] = list(zip(self.df.Date,self.df.Hash))


    def get_datehashes(self):
        return sorted(list(set(self.df['DateHash'].tolist())))


    def weak_scaling_one_commit(self, commit):
        sub_df = self.df[self.df.Hash == commit]
        #print(sub_df)

        date = sub_df.Date.tolist()[0]

        ax = sub_df.plot(kind='line', x='NP', y='Total',
                         marker='o', color='b')
        ax.set(xlabel="NP", ylabel="Time(s)")
        ax.set(xlim=[0,25])
        ax.set(title="MFiX-Exa Weak Scaling {date} {commit}".format(date=date, commit=commit))
        fig = ax.get_figure()
        fig.savefig("{date}_{commit}.png".format(date=date, commit=commit))


    def weak_scaling_over_time(self, num_proc_list=[1], case=None,
                                start_date=None, end_date=None, func_name=None):
        '''case is a string of the casename, used in plot title (ex 'HCS')
        date format is a string yyyymmdd
        num_proc_list = list containing processor counts to plot (ex [1, 2, 4, 8, 16, 32])
        num_funcs = string that contains names of a function (dataframe column name)'''

        fig, ax = plt.subplots()
        sub_df = self.df

        if not start_date:
            start_date = sorted(self.df.Date.tolist())[0]
        if not end_date:
            end_date = sorted(self.df.Date.tolist())[-1]
        if not func_name:
            func_name = 'Total'

        # Get x ticks (account for missing points)
        sub_df = sub_df[sub_df['Date'] >= start_date]
        sub_df = sub_df[sub_df['Date'] <= end_date]
        datehash = sorted(list(set(sub_df['DateHash'].tolist())))

        # Get data for a specific NP between start and end dates, sort by commit date
        for num_proc in num_proc_list:

            sub_df = self.df[self.df.NP == num_proc]
            sub_df = sub_df[sub_df['Date'] >= start_date]
            sub_df = sub_df[sub_df['Date'] <= end_date]
            sub_df = sub_df.sort_values(by=['DateHash'])

            # Plot x points so they're alligned with xticks properly (fixes issues with missing points)
            sub_df['x_vals'] = [datehash.index(x) for x in sub_df['DateHash']]
            ax = sub_df.plot(ax=ax, kind='line', x='x_vals', y=func_name,
                            label=num_proc, marker=".")



        ax.set(title="{case} {func_name} Time vs Commit from {start} to {end}".format(case=case,
                            func_name=func_name, start=start_date, end=end_date))
        ax.set(xlabel="Date, Commit", ylabel="Total Time (s)")
        ax.set_xticklabels(datehash, rotation=30, horizontalalignment='right')
        ax.set_xticks(list(range(0, len(datehash))))
        ax.set_xlim(-0.1, len(datehash)-0.9)
        patches, labels = ax.get_legend_handles_labels()
        lgd = ax.legend(patches, labels, title="NP", loc='upper left', bbox_to_anchor=(1,1))
        fig = ax.get_figure()
        fig.savefig("{case}_{func_name}_{start}_{end}.png".format(case=case,
                            func_name=func_name, start=start_date, end=end_date),
                    bbox_extra_artists=(lgd,), bbox_inches='tight')


#
##https://stackoverflow.com/questions/29233283/plotting-multiple-lines-with-pandas-dataframe
#
