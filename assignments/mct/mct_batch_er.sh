#!/bin/bash
#============ Slurm Options ===========
#SBATCH --job-name=mct-er
#SBATCH --partition=netsi_standard
#SBATCH --ntasks=1
#SBATCH --array=0-831
#SBATCH --output=./slurm-out/job_output_%A_%a.out
#SBATCH --cpus-per-task=1
#SBATCH --mail-user=ueda.m@northeastern.edu
#SBATCH --mail-type=END
#=======================================

## Clear current env/modules
#conda deactivate
module purge

## Load required module from Discovery
# module load discovery mamba
module load discovery anaconda3/2022.05

source activate /work/netsi/ueda.m/conda/netsci

cd ~/work/network-science-data/assignments/assignment3/

python mct.py --graph_type "ER" --niter 1000 --items_per_task 1500