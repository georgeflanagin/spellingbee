#!/bin/bash -e
#SBATCH --job-name=BEE10
#SBATCH --time=15:00
#SBATCH --cpus-per-task=50
#SBATCH --mem=10G

#SBATCH --mail-type=ALL
#SBATCH --mail-user=yournetid@richmond.edu

echo "I ran on: $SLURM_NODELIST"
echo "Starting at `date`"

cd ~/demoproject
/usr/bin/time python bee.py --cpus 50 --batch -d 20k.txt

echo "Finished at `date`"
