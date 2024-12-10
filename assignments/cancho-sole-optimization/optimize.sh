#!/bin/bash
#============ Slurm Options ===========
#SBATCH --partition=netsi_standard
#SBATCH --output=/home/ueda.m/discovery/slurm/logs/slurm-%j.out
#SBATCH --cpus-per-task=1
#SBATCH --array=1-100
#=======================================

module purge

# Load required module from Discovery
module load discovery mamba/1.5.9

# For debugging
echo "PATH after loading modules:"
echo $PATH

# Activate any necessary environments
source activate /work/netsi/ueda.m/conda/netsci

cd ~/final-project/

/home/ueda.m/work/conda/netsci/bin/python3 optimize.py
