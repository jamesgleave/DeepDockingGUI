#!/bin/bash
cd $1
mkdir docked
echo Transfering docked training
cat res/*train*/results/sdf/*sdf >> docked/train_docked.sdf

echo Transfering docked validation
cat res/*valid*/results/sdf/*sdf >> docked/valid_docked.sdf

echo Transfering docked testing
cat res/*test*/results/sdf/*sdf >> docked/test_docked.sdf

echo Done