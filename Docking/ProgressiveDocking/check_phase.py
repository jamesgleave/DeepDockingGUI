import os
import sys
import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-pf','--phase_file',required=True)
parser.add_argument('-itr','--iteration_directory',required=True)
io_args = parser.parse_args()

pf = io_args.phase_file
itr = io_args.iteration_directory

print(pf,itr)

if os.path.isfile(itr+'/'+pf)==False:
    with open(itr+'/'+pf,'w') as ref:
        ref.write(pf.split('.')[0]+'\n')

while 1 == 1:
    with open(itr+'/'+pf,'r') as ref:
        name = ref.readline().strip()
    if name == 'finished':
        sys.exit()
    else:
        time.sleep(60)


