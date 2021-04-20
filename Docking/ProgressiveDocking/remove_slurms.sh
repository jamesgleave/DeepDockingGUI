echo Removing Slurms

if [ "$1" = "full" ]; then
  rm -r slurm_out_files
fi

rm slurm-*