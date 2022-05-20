#!/bin/bash -e
#SBATCH --job-name=plenum8
#SBATCH --time=1:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=1G
#SBATCH --partition=parish
#SBATCH --account=gflanagi
#SBATCH --begin=now

#SBATCH --mail-type=ALL
#SBATCH --mail-user=gflanagi@richmond.edu

#SBATCH --output=%x.%j.out
#SBATCH --error=%x.%j.err

echo "I ran on: $SLURM_NODELIST"
echo "Starting at `date`"

mkdir -p /scratch/gflanagi

cd $HOME

/usr/bin/time /usr/local/sw/bee/bee.exe --cpus 8 --batch -d /scratch/slurmdemos/20k.txt

echo "Finished at `date`"
