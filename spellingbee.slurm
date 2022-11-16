#!/bin/bash -e
#SBATCH --job-name=BEE
#SBATCH --time=15:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=10G

#SBATCH --partition=medium
##SBATCH --nodelist=spdr10

#SBATCH --mail-type=ALL
#SBATCH --mail-user="hpc@richmond.edu"

echo "I ran on: $SLURM_NODELIST"
echo "Starting at `date`"

cd /home/installer/spellingbee

/usr/bin/time python bee.py --cpus 8 --db bee.db --batch -d dukedict.txt.bee > badrecords.txt

echo "Finished at `date`"
