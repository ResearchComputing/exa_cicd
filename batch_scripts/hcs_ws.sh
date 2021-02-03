#!/bin/bash
#SBATCH --nodes 2
#SBATCH --exclusive
#SBATCH --account ucb1_summit4
#SBATCH --time 08:00:00
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
ml singularity/3.6.4 gcc/8.2.0 openmpi_2.1.6

cd /scratch/summit/holtat/singularity
singularity pull --allow-unsigned --force library://aarontholt/default/mfix-exa:${BRANCH}_${COMMIT_HASH}

export MFIX=/app/mfix/build/mfix
export IMAGE=/scratch/summit/holtat/singularity/mfix-exa_${BRANCH}_${COMMIT_HASH}.sif
export MPIRUN=/pl/active/mfix/holtat/openmpi-2.1.6-install/bin/mpirun

declare -a options_array=("normal" "morton" "adapt" "combined")
declare -a dir_array=("np_0001" "np_0008" "np_0027")

for dir in "${dir_array[@]}"
do


    # Make directory if needed
    mkdir -p $WD/$dir
    cd $WD/$dir
    pwd

    #Remove old results
    rm -rf flubed*
    rm -rf normal*
    rm -rf adapt*
    rm -rf morton*
    rm -rf combined*
    # Get np from dir
    np=${dir:(-4)}
    np=$((10#$np))

    # Run default then timestepping
    $MPIRUN -np $np singularity exec $IMAGE bash -c "$MFIX inputs amr.plot_file=normal >> ${RUN_DATE}_${COMMIT_HASH}_${dir}_normal"
    $MPIRUN -np $np singularity exec $IMAGE bash -c "$MFIX inputs mfix.use_tstepadapt=1 amr.plot_file=adapt >> ${RUN_DATE}_${COMMIT_HASH}_${dir}_adapt"
    $MPIRUN -np $np singularity exec $IMAGE bash -c "$MFIX inputs mfix.sorting_type=1 amr.plot_file=morton >> ${RUN_DATE}_${COMMIT_HASH}_${dir}_morton"
    $MPIRUN -np $np singularity exec $IMAGE bash -c "$MFIX inputs mfix.sorting_type=1 mfix.use_tstepadapt=1 amr.plot_file=combined >> ${RUN_DATE}_${COMMIT_HASH}_${dir}_combined"

done


# Use elasticsearch environment
ml python_3.8.2 git
source /projects/holtat/CICD/cicd_py38_env/bin/activate

# Update repo on projects if needed
cd /projects/holtat/CICD/exa_cicd/Elasticsearch
git pull

## Index results in ES
for dir in "${dir_array[@]}"
do
    export VIDEO_BASE="/videos/${ES_INDEX}/${dir}/${BRANCH}_${COMMIT_HASH}_${RUN_DATE}"
    export URL_BASE="/images/${ES_INDEX}/${dir}/${BRANCH}_${COMMIT_HASH}_${RUN_DATE}"
    export np=${dir:(-4)}

    for option in "${options_array[@]}"
    do
        python3 output_to_es.py --es-index $ES_INDEX --work-dir $WD --np $np \
          --git-hash $COMMIT_HASH --git-branch $BRANCH --sing-image-path $IMAGE \
          --validation-image-url "${URL_BASE}_${option}.png" \
          --video-url "${VIDEO_BASE}_${option}.avi" \
          --mfix-output-path "$WD/$dir/${RUN_DATE}_${COMMIT_HASH}_${dir}_${option}" --type $option
    done
done

#http://mfix-nginx.rc.int.colorado.edu:80{{rawValue}}
#/projects/jenkins/images/mfix-hcs-5k/np_0001/phase2-develop_6a57e5f_2019-12-04_13:21:27.png

## Plot results
export HCS_ANALYZE=/projects/holtat/CICD/exa_cicd/python_scripts/hcs_analyze.py
for dir in "${dir_array[@]}"
do

    export PLOTFILE_BASE="/projects/jenkins/images/${ES_INDEX}/${dir}/${BRANCH}_${COMMIT_HASH}_${RUN_DATE}"
    echo "Plot locations: ${PLOTFILE_BASE}"

    cd $WD/$dir
    rm -rf *.old.*

    # Get processor count without leading zeros
    num_process=${dir:(-4)}
    num_process=$(echo $num_process | sed 's/^0*//')

    # ld is ratio of box size to particle size, box ratio increases by cube root of processor count
    export box_ratio=`perl -E "say ${num_process}**(1/3)"`
    export LD=$(($box_ratio*64))

    # Each lin in particle_input.dat represents a particle (minus header)
    export NUM_PARTICLES=$(($(wc -l particle_input.dat | awk '{print $1;}')-1))

    for option in "${options_array[@]}"
    do
        python3 $HCS_ANALYZE -pfp "${option}*" -np $NUM_PARTICLES -e 0.8 -T0 1000 -diap 0.01 --rho-s 1.0 --rho-g 0.001 --mu-g 0.0002 --ld $LD --outfile "${PLOTFILE_BASE}_${option}.png"
    done
done
#python3 /home/aaron/exa_cicd/python_scripts/hcs_analyze.py -pfp "plt*" -np 5050 -e 0.8 -T0 1000 -diap 0.01 --rho-s 1.0 --rho-g 0.001 --mu-g 0.0002 --ld 64 --outfile haff.png


## Paraview Videos
ml purge
deactivate

export PVPYTHON=/projects/jenkins/ParaView-5.8.0-osmesa-MPI-Linux-Python3.7-64bit/bin/pvpython
export PARAVIEW_ANIMATE=/projects/holtat/CICD/exa_cicd/python_scripts/paraview_animation.py


for dir in "${dir_array[@]}"
do
    case "${dir}" in
        np_0001)
            export focal_point=0.0032
            export position=0.025
            ;;
        np_0008)
            export focal_point=0.0064
            export position=0.050
            ;;
        np_0027)
            export focal_point=0.0096
            export position=0.080
            ;;
    esac

    for option in "${options_array[@]}"
    do
        $PVPYTHON $PARAVIEW_ANIMATE \
              --outfile="/projects/jenkins/videos/${ES_INDEX}/${dir}/${BRANCH}_${COMMIT_HASH}_${RUN_DATE}_${option}.avi" \
              --plot-file-prefix="/scratch/summit/holtat/hcs_5k_ws/${dir}/${option}" \
              --low-index=0 \
              --high-index=900 \
              --index-step=25 \
              --camera-focal-point $focal_point $focal_point $focal_point \
              --camera-position $focal_point $focal_point $position
    done
done
