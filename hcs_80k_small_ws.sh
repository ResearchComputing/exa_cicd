#!/bin/bash
#SBATCH --nodes 1
#SBATCH --exclusive
#SBATCH --account ucb1_summit2
#SBATCH --time 04:00:00
#SBATCH --output /scratch/summit/holtat/exa_slurm_output/hcs_80k_small_ws_%j

#Input to Commit number
export COMMIT=$1

echo 'COMMIT'
echo $COMMIT

source /etc/profile.d/lmod.sh
ml singularity/3.0.2 gcc/6.1.0

cd /scratch/summit/holtat/singularity
singularity pull library://aarontholt/default/mfix-exa:develop_${COMMIT}

export MFIX=/app/mfix/build/mfix/mfix
export WD=/scratch/summit/holtat/hcs_80k_small_weak_scaling
export IMAGE=/scratch/summit/holtat/singularity/mfix-exa_develop_${COMMIT}.sif
export MPIRUN=/projects/holtat/spack/opt/spack/linux-rhel7-x86_64/gcc-6.1.0/openmpi-2.1.2-foemyxg2vl7b3l57e7vhgqtlwggubj3a/bin/mpirun

## Formatting for output files
## Latest commit date, format: 2018-02-19 12:44:03 -0800
singularity exec $IMAGE bash -c "cd /app/mfix; git log -n 1 --pretty=format:'%ai'" > ${COMMIT}_info.txt
printf "\n" >> ${COMMIT}_info.txt
## Shortened latest commit hash, format: b119a72
singularity exec $IMAGE bash -c "cd /app/mfix; git log -n 1 --pretty=format:'%h'" >> ${COMMIT}_info.txt
printf "\n" >> ${COMMIT}_info.txt
## Nodelist
echo $SLURM_NODELIST >> ${COMMIT}_info.txt
printf "\n" >> ${COMMIT}_info.txt
## Modules
ml 2>&1 | grep 1 >> ${COMMIT}_info.txt

export DATE=$(sed '1q;d' ${COMMIT}_info.txt | awk '{print $1;}')
export HASH=$(sed '2q;d' ${COMMIT}_info.txt)
echo $DATE
echo $HASH
echo $SLURM_NODELIST

mkdir -p /projects/holtat/CICD/results/hcs_80k_small_weak_scaling/metadata
cp ${COMMIT}_info.txt /projects/holtat/CICD/results/hcs_80k_small_weak_scaling/metadata/${DATE}_${HASH}.txt

for dir in {np_00001,np_00004,np_00008,np_00016,np_00024}; do

    # Make dir if needed
    mkdir -p $WD/$dir
    cd $WD/$dir
    pwd
    # Get np from dir
    np=${dir:(-5)}
    np=$((10#$np))
    $MPIRUN -np $np singularity exec $IMAGE bash -c "$MFIX inputs >> ${DATE}_${HASH}_${dir}"

done


## Copy results to projects
cd $WD
for dir in {np_00001,np_00004,np_00008,np_00016,np_00024}; do
    mkdir -p /projects/holtat/CICD/results/hcs_80k_small_weak_scaling/${dir}
    cp ${dir}/${DATE}_${HASH}* /projects/holtat/CICD/results/hcs_80k_small_weak_scaling/${dir}/
done

#for ii in np_*; do cp -v $ii/2018* /projects/holtat/CICD/results/weak_scaling_small/${ii}/; done
