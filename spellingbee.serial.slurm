#!/bin/bash -e
#SBATCH --job-name=BEE50
#SBATCH --time=15:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=10G

#SBATCH --mail-type=ALL
#SBATCH --mail-user=yournetid@richmond.edu

echo "I ran on: $SLURM_NODELIST"
echo "Starting at `date`"

cd ~/demo.project
/usr/bin/time python bee.py --cpus 1 --batch -d 20k.txt

echo "Finished at `date`"
