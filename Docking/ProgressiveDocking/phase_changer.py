import os
import time
import glob
import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('-pf', '--phase_file', required=True)
parser.add_argument('-itr', '--iteration_directory', required=True)
io_args = parser.parse_args()
pf = io_args.phase_file
itr_dir = io_args.iteration_directory

print("Phase Changer:")
print("    - Monitoring: {}".format(pf))
print("    - Project: {}".format(itr_dir.split("/")[-2] + "/" + itr_dir.split("/")[-1]))

if pf == 'phase_1.sh' or pf == 'phase_a.sh':
    # Change the phase_1.sh file.
    with open(itr_dir + '/' + pf, 'w') as ref:
        ref.write('finished\n')
    print("    - Finished... File Updated")

elif pf == 'phase_2.sh':

    # Check to see if the slurm jobs are done
    while True:
        try:
            # Check every slurm file in chunk_smi
            finished_jobs = 0
            running_jobs = glob.glob(itr_dir + '/chunk*/*/slurm*.out')
            for running in running_jobs:
                # open the out file
                with open(running) as file:
                    # check if it is finished
                    lines = file.readlines()
                    if len(lines) > 0 and "finished" in lines[-1]:
                        finished_jobs += 1

            # if they are all finished, break the loop and finish phase 2
            if len(running_jobs) == finished_jobs and len(running_jobs) > 0:
                break
            else:
                time.sleep(30)
        except OSError:
            time.sleep(30)

    # update the phase file
    with open(itr_dir + '/' + pf, 'w') as ref:
        ref.write('finished\n')

elif pf == 'phase_3.sh':
    # Check to see if the slurm jobs are done
    while True:
        try:
            # Check every slurm file in res
            finished_jobs = 0
            running_jobs = glob.glob(itr_dir + '/res*/*/slurm*.out')
            for running in running_jobs:
                # open the out file
                with open(running) as file:
                    # check if it is finished
                    lines = file.readlines()
                    if len(lines) > 0 and "finished" in lines[-1]:
                        finished_jobs += 1

            # if they are all finished, break the loop and finish phase 2
            if len(running_jobs) == finished_jobs and len(running_jobs) > 0:
                break
            else:
                time.sleep(60)
        except IOError:
            time.sleep(60)

    # Perform the final phase 3 operation
    print("Wrapping up phase 3...")
    os.system("bash phase_3_concluding_combination.sh " + itr_dir)

    # update the phase file
    with open(itr_dir + '/' + pf, 'w') as ref:
        ref.write('finished\n')

elif pf == 'phase_4.sh':
    while True:
        t_jobs = len(glob.glob(itr_dir + '/simple_job/*.sh'))
        t_done = len(glob.glob(itr_dir + '/simple_job/*.out'))
        print("total jobs:", t_jobs, "total jobs done:", t_done)
        if t_done != t_jobs:
            time.sleep(60)
        else:
            jobids = []
            for f in glob.glob(itr_dir + '/simple_job/*.out'):
                tmp = f.split(".")[-2]  # slurm-phase_4.786716.out -> ['slurm-phase_4', 786716, out] -> 786716
                jobids.append(os.system('squeue|grep ' + tmp))  # gets the job id from the slurm queue

            if np.sum(np.array(jobids) > 0) == len(jobids):  # 0 is returned if the grep is successful -> still running
                with open(itr_dir + '/' + pf, 'w') as ref:
                    ref.write('finished\n')
                break
            else:
                time.sleep(60)

elif pf == 'phase_5.sh':
    while 1 == 1:
        t_jobs = len(glob.glob(itr_dir + '/simple_job_predictions/*.sh'))
        t_done = len(glob.glob(itr_dir + '/simple_job_predictions/*.out'))
        if t_done != t_jobs:
            time.sleep(60)
        else:
            jobids = []
            for f in glob.glob(itr_dir + '/simple_job_predictions/*.out'):
                tmp = f.split(".")[-2]  # slurm-phase_5.786716.out -> ['slurm-phase_4', 786716, out] -> 786716
                jobids.append(os.system('squeue|grep ' + tmp))
            if np.sum(np.array(jobids) > 0) == len(jobids):
                with open(itr_dir + '/' + pf, 'w') as ref:
                    ref.write('finished\n')
                break
            else:
                time.sleep(60)

elif pf == 'final_phase.sh':
    while 1 == 1:
        all_sdfs = len(glob.glob(itr_dir + '/to_dock/sdf/*.sdf*'))
        fct = len(glob.glob(itr_dir + '/to_dock/docked/*.sdf*'))
        if fct == all_sdfs:
            with open(itr_dir + '/phase_f.sh', 'w') as ref:
                ref.write('finished\n')
            break
        else:
            time.sleep(300)

elif pf == 'final_phase_alternate.sh' or pf == 'final_phase_alternate_1.sh':
    with open(itr_dir + '/phase_f.sh', 'w') as ref:
        ref.write('finished\n')
