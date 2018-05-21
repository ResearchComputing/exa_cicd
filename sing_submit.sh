#!/bin/bash
#SBATCH --nodes 1
#SBATCH --exclusive
#SBATCH --account ucb1_summit1
#SBATCH --time 04:00:00
##SBATCH --output normal.out
#SBATCH --reservation bench-bandwidth

ml singularity/2.4.2 gcc/6.1.0

export MFIX=/app/mfix/build/mfix/mfix
export WD=/scratch/summit/holtat/sing
export IMAGE=/curc/tools/images/holtat/mfix_fulllatest.simg
export MPIRUN=/projects/holtat/spack/opt/spack/linux-rhel7-x86_64/gcc-6.1.0/openmpi-2.1.0-4wsyjochpemaio57jlxq274utszh5are/bin/mpirun

## Formatting for output files
## Latest commit date, format: 2018-02-19 12:44:03 -0800
singularity exec mfix.img bash -c "cd /app/mfix; git log -n 1 --pretty=format:'%ai' develop" > info.txt
echo '' >> info.txt
## Shortened latest commit hash, format: b119a72
singularity exec mfix.img bash -c "cd /app/mfix; git log -n 1 --pretty=format:'%h' develop" >> info.txt
echo '' >> info.txt

export DATE=$(sed '1q;d' info.txt | awk '{print $1;}')
export HASH=$(sed '2q;d' info.txt)
echo $DATE
echo $HASH

for dir in {np_00001,np_00004,np_00008,np_00016,np_00024}; do

    mkdir -p $WD/$dir
    cd $WD/$dir
    pwd
    $MPIRUN -np 24 singularity exec $IMAGE bash -c "cd $WD/$dir; $MFIX inputs >> ${DATE}_${HASH}_${dir}"

done
