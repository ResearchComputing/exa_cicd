#!/bin/bash
#SBATCH --nodes 9
#SBATCH --exclusive
#SBATCH --account ucb1_summit2
#SBATCH --time 04:00:00
#SBATCH --output /scratch/summit/holtat/exa_slurm_output/hcs_80k_large_ws_%j

#Input to Commit number
export COMMIT=$1

echo 'COMMIT'
echo $COMMIT

# Modules don't work without this
source /etc/profile.d/lmod.sh
# Custom openmpi 2.1.2 module in petalibrary
ml use /pl/active/mfix/holtat/modules
ml singularity/3.0.2 gcc/8.2.0 opempi_2.1.6

cd /scratch/summit/holtat/singularity
singularity pull library://aarontholt/default/mfix-exa:${BRANCH}_${COMMIT}

export MFIX=/app/mfix/build/mfix/mfix
export WD=/scratch/summit/holtat/hcs_200k_ws
export IMAGE=/scratch/summit/holtat/singularity/mfix-exa_${BRANCH}_${COMMIT}.sif
export MPIRUN=/projects/holtat/spack/opt/spack/linux-rhel7-x86_64/gcc-6.1.0/openmpi-2.1.2-foemyxg2vl7b3l57e7vhgqtlwggubj3a/bin/mpirun

## Formatting for output files
## Latest commit date, format: 2018-02-19 12:44:03 -0800
singularity exec $IMAGE bash -c "cd /app/mfix; git log -n 1 --pretty=format:'%ai'" > ${BRANCH}_${COMMIT}_info.txt
printf "\n" >> ${BRANCH}_${COMMIT}_info.txt
## Shortened latest commit hash, format: b119a72
singularity exec $IMAGE bash -c "cd /app/mfix; git log -n 1 --pretty=format:'%h'" >> ${BRANCH}_${COMMIT}_info.txt
printf "\n" >> ${BRANCH}_${COMMIT}_info.txt
## Nodelist
echo $SLURM_NODELIST >> ${BRANCH}_${COMMIT}_info.txt
printf "\n" >> ${BRANCH}_${COMMIT}_info.txt
## Modules
ml 2>&1 | grep 1 >> ${BRANCH}_${COMMIT}_info.txt

export DATE=$(sed '1q;d' ${BRANCH}_${COMMIT}_info.txt | awk '{print $1;}')
export HASH=$(sed '2q;d' ${BRANCH}_${COMMIT}_info.txt)
echo $DATE
echo $HASH
echo $SLURM_NODELIST

mkdir -p /projects/holtat/CICD/results/hcs_80k_large_weak_scaling/metadata
cp ${BRANCH}_${COMMIT}_info.txt /projects/holtat/CICD/results/hcs_80k_large_weak_scaling/metadata/${DATE}_${HASH}.txt

for dir in {np_00001,np_00008,np_00027}; do

    # Make directory if needed
    mkdir -p $WD/$dir
    cd $WD/$dir
    pwd
    # Get np from dir
    np=${dir:(-5)}
    np=$((10#$np))

    # Run default then timestepping
    $MPIRUN -np $np singularity exec $IMAGE bash -c "$MFIX inputs >> ${DATE}_${HASH}_${dir}"
    $MPIRUN -np $np singularity exec $IMAGE bash -c "$MFIX inputs_adapt >> ${DATE}_${HASH}_${dir}"

done


## Copy results to projects
# cd $WD
# for dir in {np_00001,np_00008,np_00027,np_00064,np_00125,np_00216}; do
#     mkdir -p /projects/holtat/CICD/results/hcs_80k_large_weak_scaling/${dir}
#     cp ${dir}/${DATE}_${HASH}* /projects/holtat/CICD/results/hcs_80k_large_weak_scaling/${dir}/
# done

#for ii in np_*; do cp -v $ii/2018* /projects/holtat/CICD/results/weak_scaling_small/${ii}/; done
