import numpy as np
import sys
from scipy.interpolate import NearestNDInterpolator
import matplotlib.pyplot as plt
import matplotlib as mpl
import glob
mpl.use("agg")


class AMReXParticleHeader(object):
    '''

    This class is designed to parse and store the information 
    contained in an AMReX particle header file. 

    Usage:

        header = AMReXParticleHeader("plt00000/particle0/Header")
        print(header.num_particles)
        print(header.version_string)

    etc...

    '''

    def __init__(self, header_filename):

        self.real_component_names = []
        self.int_component_names = []
        with open(header_filename, "r") as f:
            self.version_string = f.readline().strip()

            particle_real_type = self.version_string.split('_')[-1]
            particle_real_type = self.version_string.split('_')[-1]
            if particle_real_type == 'double':
                self.real_type = np.float64
            elif particle_real_type == 'single':
                self.real_type = np.float32
            else:
                raise RuntimeError("Did not recognize particle real type.")
            self.int_type = np.int32

            self.dim = int(f.readline().strip())
            self.num_int_base = 2
            self.num_real_base = self.dim
            self.num_real_extra = int(f.readline().strip())
            for i in range(self.num_real_extra):
                self.real_component_names.append(f.readline().strip())
            self.num_int_extra = int(f.readline().strip())
            for i in range(self.num_int_extra):
                self.int_component_names.append(f.readline().strip())
            self.num_int = self.num_int_base + self.num_int_extra
            self.num_real = self.num_real_base + self.num_real_extra
            self.is_checkpoint = bool(int(f.readline().strip()))
            self.num_particles = int(f.readline().strip())
            self.max_next_id = int(f.readline().strip())
            self.finest_level = int(f.readline().strip())
            self.num_levels = self.finest_level + 1

            if not self.is_checkpoint:
                self.num_int_base = 0
                self.num_int_extra = 0
                self.num_int = 0

            self.grids_per_level = np.zeros(self.num_levels, dtype='int64')
            for level_num in range(self.num_levels):
                self.grids_per_level[level_num] = int(f.readline().strip())

            self.grids = [[] for _ in range(self.num_levels)]
            for level_num in range(self.num_levels):
                for grid_num in range(self.grids_per_level[level_num]):
                    entry = [int(val) for val in f.readline().strip().split()]
                    self.grids[level_num].append(tuple(entry))

def get_time_stamp(fldfname):

    infile=open(fldfname+"/Header",'r')

    infile.readline() #Hyperclaw-v1.1
    nvars=int(infile.readline().split()[0])

    for i in range(nvars):
        line=infile.readline()

    line=infile.readline() #3 (3 d coords?)

    time=float(infile.readline().split()[0])
    return(time)

def read_amrex_binary_particle_file(fn, ptype="particles"):

    timestamp=get_time_stamp(fn)
    base_fn = fn + "/" + ptype
    header = AMReXParticleHeader(base_fn + "/Header")

    
    idtype = "(%d,)i4" % header.num_int    
    if header.real_type == np.float64:
        fdtype = "(%d,)f8" % header.num_real
    elif header.real_type == np.float32:
        fdtype = "(%d,)f4" % header.num_real
    
    idata = np.empty((header.num_particles, header.num_int ))
    rdata = np.empty((header.num_particles, header.num_real))
    
    ip = 0
    for lvl, level_grids in enumerate(header.grids):
        for (which, count, where) in level_grids:
            if count == 0: continue
            fn = base_fn + "/Level_%d/DATA_%05d" % (lvl, which)

            with open(fn, 'rb') as f:
                f.seek(where)
                if header.is_checkpoint:
                    ints   = np.fromfile(f, dtype = idtype, count=count)
                    idata[ip:ip+count] = ints

                floats = np.fromfile(f, dtype = fdtype, count=count)
                rdata[ip:ip+count] = floats            
            ip += count

    return idata, rdata, timestamp


if __name__ == "__main__":

    fn_pattern = sys.argv[1]

    xloc=0.025 #2.5 cm height
    fac=0.1 #grab particles within 10% of xloc

    ymin=0.0
    ymax=0.044
    zmin=0.0
    zmax=0.011

    xsample_min=xloc*(1-fac)
    xsample_max=xloc*(1+fac)

    fn_list = sorted(glob.glob(fn_pattern), key=lambda f: int(f.split("flubed")[1]))
    nfiles=len(fn_list)

    
    nsample_pts_y=50
    dy=(ymax-ymin)/(nsample_pts_y-1.0)
    
    nsample_pts_z=10
    dz=(zmax-zmin)/(nsample_pts_z-1.0)

    yarray=np.linspace(ymin,ymax,nsample_pts_y)
    
    velarray=np.zeros(nsample_pts_y)
    avgvelarray=np.zeros(nsample_pts_y)

    
    for i, fn in enumerate(fn_list):
        print("reading %s"%(fn))
        idata, rdata, timestamp = read_amrex_binary_particle_file(fn)
        ppos = rdata[:,0:3]   # assumes 3D
        xvel = rdata[:,3]
        yvel = rdata[:,4]
        zvel = rdata[:,5]

        relevant_pids=[]
        npart=len(xvel)

        for i in range(npart):
            if((ppos[i,0] >= xsample_min) and (ppos[i,0] <= xsample_max)):
                relevant_pids.append(i)

        npts=len(relevant_pids)
        points=np.zeros((npts,3))
        interp_vel=np.zeros(npts)

        print("npts:",npts)

        for npt in range(npts):
            interp_vel[npt]=xvel[relevant_pids[npt]]
            points[npt][0]=ppos[relevant_pids[npt],0]
            points[npt][1]=ppos[relevant_pids[npt],1]
            points[npt][2]=ppos[relevant_pids[npt],2]

        fn = NearestNDInterpolator(points, interp_vel)

        velarray[:]=0.0
        for npty in range(nsample_pts_y):

            #average along z direction
            for nptz in range(nsample_pts_z):
                value=fn(xloc,yarray[npty],zmin+nptz*dz)
                velarray[npty] += value

            velarray[npty] /= nptz

        avgvelarray = avgvelarray+velarray

    avgvelarray=avgvelarray/nfiles

    #read experimental data
    yexpt=np.array([])
    velexpt=np.array([])

    infile=open("exptdata_vel.dat","r")
    for line in infile:
        yexpt=np.append(yexpt,float(line.split()[0]));
        velexpt=np.append(velexpt,float(line.split()[1]));
    infile.close()


    #matplotlib plotting
    font={'family':'Helvetica', 'size':'15'}
    mpl.rc('font',**font)
    mpl.rc('xtick',labelsize=15)
    mpl.rc('ytick',labelsize=15)

    plt.ylim([-0.3,0.5])
    plt.plot(yarray,avgvelarray,'k-',lw=2,label="simulation")
    plt.plot(yexpt,velexpt,'^',markersize=6,label="Experiment (Muller et al.)")
    plt.xlabel("distance (m)")
    plt.ylabel("Average particle speed (m/s)")
    plt.legend()
    plt.tight_layout()
    #plt.show()
    plt.savefig("muller_flubedvel_2.5cm.png")

    outfile=open("velprofile.dat","w")
    for npty in range(nsample_pts_y):
        outfile.write("%e\t%e\n"%(yarray[npty],avgvelarray[npty]))

    outfile.close()
