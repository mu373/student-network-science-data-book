#!/bin/bash
#============ Slurm Options ===========
#SBATCH --job-name=tsp-parallel
#SBATCH --partition=netsi_standard
#SBATCH --ntasks=1
#SBATCH --array=1-100
#SBATCH --output=./slurm-out/job_output_%A_%a.out
#SBATCH --cpus-per-task=1
#SBATCH --mail-user=ueda.m@northeastern.edu
#SBATCH --mail-type=END
#=======================================

## Clear current env/modules
#conda deactivate
module purge

## Load required module from Discovery
module load discovery mamba
# module load discovery anaconda3/2022.01

source activate /work/netsi/ueda.m/conda/netsi

datasets=("berlin52" "brazil58" "brg180" "gr229" "pr439")

# Change "dataset" by the task id
dataset_index=$(( (SLURM_ARRAY_TASK_ID - 1) / 20 ))
dataset=${datasets[$dataset_index]}

python tsp.py --jobid $SLURM_ARRAY_TASK_ID --data $dataset
