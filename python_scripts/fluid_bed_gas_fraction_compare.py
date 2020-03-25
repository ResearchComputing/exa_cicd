# Original code by: Hari Sitaraman
# Modified by Aaron Holt
# MFiX-Exa velocity comparison for the 2.5cm Muller fluid bed
## Experimental data file: exptdata_epg.dat
## python3 fluid_bed_gas_fraction_compare.py -pfp "flubed*" --outfile "fbed_vel.png"

import argparse
import os
import glob
import yt
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib as mpl
import matplotlib.colors as colors

from sys import argv
from yt.funcs import mylog
mylog.setLevel(40) # This sets the log level to "ERROR"
mpl.use("agg")


parser = argparse.ArgumentParser(description='Velocity comparison files for the 2.5cm Muller fluid bed')
parser.add_argument('-pfp', '--plot-file-pattern', dest='pfp', type=str, required=True, help='Plot file pattern prefix glob (ex: plt*)')
parser.add_argument('--outfile', dest='outfile', type=str, required=True, help='Path to save velocity plot file')
args = parser.parse_args()

# Remove old files if they exist
for fname in ['epg_line.dat', args.outfile]:
    try:
        os.remove(fname)
    except:
        pass

fn_list = sorted(glob.glob(args.pfp), key=lambda f: int(f.split(args.pfp[0:-1])[1]))


xloc=0.0164
y_min=0.0
y_max=0.044
z_min=0.0
z_max=0.011

ds = yt.load(fn_list[0])
mid=np.array([0.5*(y_min+y_max),0.5*(z_min+z_max)])
L=np.array([y_max-y_min,z_max-z_min])
dxmin = ds.index.get_smallest_dx()
res=np.array([int(L[0]/dxmin),int(L[1]/dxmin)])
# print(res)

fields_load=["ep_g"]
epgavg=np.zeros((res[1],res[0]))

for i, fn in enumerate(fn_list):

    ds = yt.load(fn)

    slc = yt.SlicePlot(ds, 'x', fields_load,center=[xloc,mid[0],mid[1]])
    frb = slc.data_source.to_frb(((L[0],'cm'),(L[1],'cm')), res)
    epg=np.array(frb["ep_g"])
    epgavg += epg

epgavg=epgavg/float(len(fn_list))
lineavg=np.mean(epgavg,0)

#remove corner data
#lineavg[0]=np.mean(epgavg[1:-1,0])
#lineavg[-1]=np.mean(epgavg[1:-1,-1])

#read experimental data
yexpt=np.array([])
epgexpt=np.array([])

infile=open("exptdata_epg.dat","r")
for line in infile:
    yexpt=np.append(yexpt,float(line.split()[0]));
    epgexpt=np.append(epgexpt,float(line.split()[1]));
infile.close()

#matplotlib plotting
font={'family':'Helvetica', 'size':'15'}
mpl.rc('font',**font)
mpl.rc('xtick',labelsize=15)
mpl.rc('ytick',labelsize=15)

yarray=np.array([])
for i in range(len(lineavg)):
    yloc=y_min+dxmin*(i+0.5)
    yarray=np.append(yarray,yloc)

plt.ylim([0.4,0.8])
plt.plot(yarray,lineavg,'k-',lw=2,label="simulation")
plt.plot(yexpt,epgexpt,'^',markersize=8,label="Experiment (Muller et al.)")
plt.xlabel("distance (m)")
plt.ylabel("Gas fraction")
plt.legend()
plt.tight_layout()
#plt.show()
plt.savefig(args.outfile)

outfile=open("epg_line.dat","w")
for i in range(len(lineavg)):
    outfile.write("%e\t%e\n"%(yarray[i],lineavg[i]))
outfile.close()
