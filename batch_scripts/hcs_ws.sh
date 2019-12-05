#!/bin/bash
#SBATCH --nodes 2
#SBATCH --exclusive
#SBATCH --account ucb1_summit3
#SBATCH --time 04:00:00
#SBATCH --output /scratch/summit/holtat/exa_slurm_output/hcs_200k_ws_%j

#Inputs
export COMMIT=$1
export WD=$2
export ES_INDEX=$3

echo 'COMMIT'
echo $COMMIT

# Modules don't work without this
source /etc/profile.d/lmod.sh
# Custom openmpi 2.1.2 module in petalibrary
ml use /pl/active/mfix/holtat/modules
ml singularity/3.3.0 gcc/8.2.0 openmpi_2.1.6

cd /scratch/summit/holtat/singularity
singularity pull --allow-unsigned --force library://aarontholt/default/mfix-exa:${BRANCH}_${COMMIT}

export MFIX=/app/mfix/build/mfix/mfix
export IMAGE=/scratch/summit/holtat/singularity/mfix-exa_${BRANCH}_${COMMIT}.sif
export MPIRUN=/pl/active/mfix/holtat/openmpi-2.1.6-install/bin/mpirun

## Formatting for output files
## Latest commit date, format: 2018-02-19 12:44:03 -0800
cd $WD
singularity exec $IMAGE bash -c "cd /app/mfix; git log -n 1 --pretty=format:'%ai'" > ${BRANCH}_${COMMIT}_info.txt
printf "\n" >> ${BRANCH}_${COMMIT}_info.txt
## Shortened latest commit hash, format: b119a72
singularity exec $IMAGE bash -c "cd /app/mfix; git log -n 1 --pretty=format:'%h'" >> ${BRANCH}_${COMMIT}_info.txt
printf "\n" >> ${BRANCH}_${COMMIT}_info.txt
## Nodelist
echo $SLURM_NODELIST >> ${BRANCH}_${COMMIT}_info.txt
printf "\n" >> ${BRANCH}_${COMMIT}_info.txt
## JobID
echo $SLURM_JOBID >>${BRANCH}_${COMMIT}_info.txt
printf "\n"
## Modules
ml 2>&1 | grep 1 >> ${BRANCH}_${COMMIT}_info.txt

export COMMIT_DATE=$(sed '1q;d' ${BRANCH}_${COMMIT}_info.txt | awk '{print $1;}')
export HASH=$(sed '2q;d' ${BRANCH}_${COMMIT}_info.txt)
echo $COMMIT_DATE
echo $HASH
echo $SLURM_NODELIST

#mkdir -p /projects/holtat/CICD/results/hcs_80k_large_weak_scaling/metadata
#cp ${BRANCH}_${COMMIT}_info.txt /projects/holtat/CICD/results/hcs_80k_large_weak_scaling/metadata/${DATE}_${HASH}.txt

for dir in {np_0001,np_0008,np_0027}; do

    # Make directory if needed
    mkdir -p $WD/$dir
    cd $WD/$dir
    pwd
    # Get np from dir
    np=${dir:(-4)}
    np=$((10#$np))

    # Run default then timestepping
    $MPIRUN -np $np singularity exec $IMAGE bash -c "$MFIX inputs >> ${COMMIT_DATE}_${HASH}_${dir}"
    $MPIRUN -np $np singularity exec $IMAGE bash -c "$MFIX inputs_adapt >> ${COMMIT_DATE}_${HASH}_${dir}_adapt"

##mfix.use_tstepadapt=0
    #Consider mpirun -np $np --map-by node ...

done


# Use elasticsearch environment
ml python/3.5.1 intel/17.4 git
source /projects/holtat/CICD/elastic_env/bin/activate

# Update repo on projects if needed
cd /projects/holtat/CICD/exa_cicd/Elasticsearch
git pull

## Index results in ES
for dir in {np_0001,np_0008,np_0027}; do

    export RUN_DATE=$(date '+%Y-%m-%d_%H:%M:%S')
    export URL_BASE="/images/${ES_INDEX}/np_${np}/${BRANCH}_${HASH}_${RUN_DATE}"

    np=${dir:(-4)}
    python3 output_to_es.py --es-index $ES_INDEX --work-dir $WD --np $np --commit-date $COMMIT_DATE \
      --git-hash $HASH --git-branch $BRANCH --sing-image-path $IMAGE \
      --validation-image-url "${URL_BASE}.png"
    python3 output_to_es.py --es-index $ES_INDEX --work-dir $WD --np $np --commit-date $COMMIT_DATE \
      --git-hash $HASH --git-branch $BRANCH --sing-image-path $IMAGE \
      --validation-image-url "${URL_BASE}_adapt.png" --type adapt

done

## Copy results to projects
# cd $WD
# for dir in {np_00001,np_00008,np_00027,np_00064,np_00125,np_00216}; do
#     mkdir -p /projects/holtat/CICD/results/hcs_80k_large_weak_scaling/${dir}
#     cp ${dir}/${DATE}_${HASH}* /projects/holtat/CICD/results/hcs_80k_large_weak_scaling/${dir}/
# done

#for ii in np_*; do cp -v $ii/2018* /projects/holtat/CICD/results/weak_scaling_small/${ii}/; done
