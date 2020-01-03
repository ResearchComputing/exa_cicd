#!/bin/bash
#SBATCH --nodes 2
#SBATCH --exclusive
#SBATCH --account ucb1_summit3
#SBATCH --time 04:00:00
#SBATCH --output /scratch/summit/holtat/exa_slurm_output/hcs_5k_ws_%j

#Inputs
export COMMIT_HASH=$1
export WD=$2
export ES_INDEX=$3
export RUN_DATE=$(date '+%Y-%m-%d_%H-%M-%S')

echo 'COMMIT_HASH'
echo $COMMIT_HASH

# Copy Mfix input files from /projects
cp -r --no-clobber /projects/holtat/CICD/hcs_5k_ws/* $WD

# Modules don't work without this
source /etc/profile.d/lmod.sh
# Custom openmpi 2.1.2 module in petalibrary
ml use /pl/active/mfix/holtat/modules
ml singularity/3.3.0 gcc/8.2.0 openmpi_2.1.6

cd /scratch/summit/holtat/singularity
singularity pull --allow-unsigned --force library://aarontholt/default/mfix-exa:${BRANCH}_${COMMIT_HASH}

export MFIX=/app/mfix/build/mfix
export IMAGE=/scratch/summit/holtat/singularity/mfix-exa_${BRANCH}_${COMMIT_HASH}.sif
export MPIRUN=/pl/active/mfix/holtat/openmpi-2.1.6-install/bin/mpirun

for dir in {np_0001,np_0008,np_0027}; do

    # Make directory if needed
    mkdir -p $WD/$dir
    cd $WD/$dir
    pwd
    # Get np from dir
    np=${dir:(-4)}
    np=$((10#$np))

    # Run default then timestepping
    $MPIRUN -np $np singularity exec $IMAGE bash -c "$MFIX inputs >> ${RUN_DATE}_${COMMIT_HASH}_${dir}"
    $MPIRUN -np $np singularity exec $IMAGE bash -c "$MFIX inputs mfix.use_tstepadapt=1 amr.plot_file=adapt >> ${RUN_DATE}_${COMMIT_HASH}_${dir}_adapt"

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

    export URL_BASE="/images/${ES_INDEX}/np_${np}/${BRANCH}_${COMMIT_HASH}_${RUN_DATE}"

    np=${dir:(-4)}
    python3 output_to_es.py --es-index $ES_INDEX --work-dir $WD --np $np \
      --git-hash $COMMIT_HASH --git-branch $BRANCH --sing-image-path $IMAGE \
      --validation-image-url "${URL_BASE}.png" \
      --mfix-output-path "$WD/$dir/${RUN_DATE}_${COMMIT_HASH}_${dir}"

    python3 output_to_es.py --es-index $ES_INDEX --work-dir $WD --np $np \
      --git-hash $COMMIT_HASH --git-branch $BRANCH --sing-image-path $IMAGE \
      --validation-image-url "${URL_BASE}_adapt.png" \
      --mfix-output-path "$WD/$dir/${RUN_DATE}_${COMMIT_HASH}_${dir}_adapt" --type adapt

done



## Plot results
export HCS_ANALYZE=/projects/holtat/CICD/exa_cicd/python_scripts/hcs_analyze.py
for dir in {np_0001,np_0008,np_0027}; do

    cd $WD/$dir
    rm -rf plt*.old*
    rm -rf adapt*.old*

    # Get processor count without leading zeros
    num_process=${dir:(-4)}
    num_process=$(echo $num_process | sed 's/^0*//')

    # ld is ratio of box size to particle size
    export LD=$(($num_process*64))

    # Each lin in particle_input.dat represents a particle (minus header)
    export NUM_PARTICLES=$(($(wc -l particle_input.dat | cut -c1-5)-1))

    python3 $HCS_ANALYZE -pfp "plt*" -np $NUM_PARTICLES -e 0.8 -T0 1000 -diap 0.01 --rho-s 1.0 --rho-g 0.001 --mu-g 0.0002 --ld $LD --outfile haff.png
    python3 $HCS_ANALYZE -pfp "adapt*" -np $NUM_PARTICLES -e 0.8 -T0 1000 -diap 0.01 --rho-s 1.0 --rho-g 0.001 --mu-g 0.0002 --ld $LD --outfile adapt.png


done
#python3 /home/aaron/exa_cicd/python_scripts/hcs_analyze.py -pfp "plt*" -np 5050 -e 0.8 -T0 1000 -diap 0.01 --rho-s 1.0 --rho-g 0.001 --mu-g 0.0002 --ld 64 --outfile haff.png
