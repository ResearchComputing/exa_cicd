## This script duplicates a rectangular geometry
## for an hcs case in mfix

import pathlib
import numpy as np

### USER INPUT SECTION ###
# Scale the problem by an integer value in each
# direction defined below
scale_x = [2, 3, 4, 5, 6]
scale_y = [2, 3, 4, 5, 6]
scale_z = [2, 3, 4, 5, 6]
#scale = [scale_x, scale_y, scale_z]

# Original file locations
orig = 'np_00001'
orig_particle_file = orig + '/particle_input.dat'
orig_mfixdat = orig + '/mfix.dat'
orig_inputs = orig + '/inputs'

# New File Locations
new = ['np_00008', 'np_00027', 'np_00064', 'np_00125', 'np_00216'] # A directory with this name is created if it doesn't exist
#new_particle = new + '/particle_input.dat'
#new_mfixdat = new + '/mfix.dat'
#new_inputs = new + '/inputs'

### END USER INPUT ###


def parse_line(my_str):
    '''takes a string an returns a list with no whitespace'''
    my_str = my_str.split(' ')
    my_str = list(filter(None, my_str))
    return my_str

def multiply_vals(line, scale):
    '''Takes a list of 3 strings and multiplies it
    by integer scalers (strings are converted to floats)'''
    line[2] = str(float(line[2])*scale[0])
    line[3] = str(float(line[3])*scale[1])
    line[4] = str(float(line[4])*scale[2])
    return line

def get_geometry(filename):
    '''takes the inputs file and returns the x, y, and z
    lengths of the problem'''
    low = []
    high = []
    dim = []

    with open(filename, 'r') as f:
        for line in f:
            line = line.lower()
            if 'geometry.prob_lo' in line:
                line = parse_line(line)
                try:
                    low = [float(x) for x in line[2:5]]
                except ValueError:
                    print('ValueError, assuming low bound 0,0,0')
                    low = [0,0,0]
            if 'geometry.prob_hi' in line:
                line = parse_line(line)
                high = [float(x) for x in line[2:5]]
        f.close()
    for ii in range(0,3):
        dim.append(high[ii] - low[ii])
    return dim


def update_geometry(orig_mfixdat, new_mfixdat,
                    orig_inputs, new_inputs,
                    dims, scale):
    '''Update mfix.dat and input file for hcs case
    based on the given scale vector'''
    

    with open(orig_inputs, 'r') as of, open(new_inputs, 'w') as nf:
        for line in of:
            if 'geometry.prob_hi' in line:
                line = parse_line(line)
                line = multiply_vals(line, scale)
                nf.write(' '.join(line) + '\n')
            elif 'amr.n_cell' in line:
                line = parse_line(line)
                line = multiply_vals(line, scale)
                line[2:5] = [str(int(float(x))) for x in line[2:5]]
                nf.write(' '.join(line) + '\n')
            else:
                nf.write(line)

        of.close()
        nf.close()
    
    with open(orig_mfixdat, 'r') as of, open(new_mfixdat, 'w') as nf:
        for line in of:
            if 'IC_X_e' in line: 
                line = parse_line(line)
                line[2] = str(float(line[2])*scale[0])
                nf.write(' '.join(line) + '\n')
            elif 'IC_Y_n' in line:
                line = parse_line(line)
                line[2] = str(float(line[2])*scale[1])
                nf.write(' '.join(line) + '\n')
            elif 'IC_Z_t' in line:
                line = parse_line(line)
                line[2] = str(float(line[2])*scale[2])
                nf.write(' '.join(line) + '\n')
            elif 'BC_' in line:
                nf.write(line.replace("0.006", str(float(0.006*scale[2]))))
            else:
                nf.write(line)
        of.close()
        nf.close()
    return



def read_particle_input(filename):
    '''Read initial particle file into a list
    input = A string filename
    outputs: list of particle information, number of particles'''
    particles = []
    num_particles = []
    with open(filename, 'r+') as f:
        for line in f:
            particles.append([int(float(line.split()[0]))] + [float(x) for x in line.split()[1:]])
        num_particles = int(particles[0][0])
        particles = particles[1:]
        f.close()
    return particles, num_particles

def write_particle_file(particles, filename):
    '''Write particle list to file'''
    with open(filename, 'w') as f:
        f.truncate()
        f.write(str(int(len(particles))) + '\n')
        for counter, line in enumerate(particles):
            line = [str(x).upper() for x in line]
            f.write(' '.join(line)+'\n')
        f.close()
    return


def duplicate(particles, num_particles, scale, dims): #,direction)
    '''Given particle data from a rectangular problem, duplicate
    the problem in a given direction. Inputs:
    scale  = [x, y, z] - integer list with amount to scale
    dimension by.
    dims = [x, y, z] - dimensions of original problem'''
    
    new_particles = []

    for lc3 in range(0, scale[2]):    
        for lc2 in range(0, scale[1]):
            for lc1 in range(0, scale[0]):
            
                # Don't append original particle
                if lc3 == 0 and lc2 == 0 and lc1 == 0:
                    continue
            
                for lc in range(0, num_particles):
                
                    new_particles.append([
                        1,
                        particles[lc][1] + float(lc1)*dims[0],
                        particles[lc][2] + float(lc2)*dims[1],
                        particles[lc][3] + float(lc3)*dims[2],
                        particles[lc][4],
                        particles[lc][5],
                        particles[lc][6],
                        particles[lc][7],
                        particles[lc][8]
                        ])
    num_particles *= scale[0]*scale[1]*scale[2]
    return orig_particles+new_particles, num_particles


#pathlib.Path(new).mkdir(parents=True, exist_ok=True) 

dims = get_geometry(orig_inputs)
orig_particles, orig_num_particles = read_particle_input(orig_particle_file)
print("Original num particles = ", orig_num_particles)

for ii in range(0, len(new)): 

    new_dir = new[ii]
    pathlib.Path(new_dir).mkdir(parents=True, exist_ok=True)
    scale = [scale_x[ii], scale_y[ii], scale_z[ii]]
    new_p_file = new_dir + '/particle_input.dat'
    new_mfixdat = new_dir + '/mfix.dat'
    new_inputs = new_dir + '/inputs'
    
    
    update_geometry(orig_mfixdat, new_mfixdat,
                    orig_inputs, new_inputs,
                    dims, scale)
   
    new_particles, new_num_particles = duplicate(orig_particles, orig_num_particles, scale, dims)
    #print("Filename, New num particles = ", new_p_file, new_num_particles)
    #print(len(particles))
    #print(particles[-1])
    
    write_particle_file(new_particles, new_p_file)
    print("Filename, New num particles = ", new_p_file, new_num_particles)







#
