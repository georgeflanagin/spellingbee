#!/bin/bash -e
#SBATCH --job-name=BEE
#SBATCH --time=15:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=10G

#SBATCH --mail-type=ALL
#SBATCH --mail-user=yournetid@richmond.edu

#SBATCH --output=%x.%j.out
#SBATCH --error=%x.%j.err

echo "I ran on: $SLURM_NODELIST"
echo "Starting at `date`"

mkdir -p /scratch/$(whoami)

cd $HOME

/usr/bin/time /usr/local/sw/bee/bee.exe --cpus 1 --batch -d /scratch/slurmdemos/20k.txt

echo "Finished at `date`"
