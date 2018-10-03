import argparse
from weak_scaling import process

parser = argparse.ArgumentParser(description='Inputs for process class')
parser.add_argument('--work-dir', dest='work_dir', type=str, help='Directory where data directories live')
parser.add_argument('--data-dirs', dest='data_dirs', nargs='+', help='List of directories to look for data in [np_00001, np_00004, ...]')
parser.add_argument('--num-funcs', dest='num_funcs', type=int, metavar='N', help='Top N most time-consuming functions to process')
parser.add_argument('--start-date', dest='start_date', type=str, help='Date in form yyyymmdd')
parser.add_argument('--end-date', dest='end_date', type=str, help='Date in form yyyymmdd')
args = parser.parse_args()

A = process(base_dir=args.work_dir,
            dir_list=args.data_dirs,
            num_funcs=args.num_funcs)


A.preprocess()
A.prefill_dict()
A.add_data_to_dict()
A.dict_to_df()
#A.weak_scaling_one_commit(commit='777730c')
#A.weak_scaling_over_time(case='HCS', num_proc_list=[1, 4, 8, 16, 24],
#         start_date=args.start_date, end_date=args.end_date)
#A.weak_scaling_over_time(case='HCS', num_proc_list=[1, 8, 27, 64, 125, 216],
#        start_date=args.start_date, end_date=args.end_date)
#A.weak_scaling_over_time(case='HCS', num_proc_list=[1, 4, 8, 16, 24], func_name='solve_bicgstab')
#A.weak_scaling_over_time(case='HCS', num_proc_list=[1, 4, 8, 16, 24], func_name='calc_particle_collisions()')


# A.weak_scaling_over_time(case='Tumbler', num_proc_list=[1, 8, 27, 64],
#                 start_date=args.start_date, end_date=args.end_date)
A.weak_scaling_one_commit(commit='5073e64')
## Switching to plotly
#A.weak_scaling_over_time_2(case='HCS', num_proc_list=[1, 4, 8, 16, 24])

##python driver.py --work-dir=/projects/holtat/CICD/results/weak_scaling_small/ --data-dirs np_00001 np_00004 np_00008 np_00016 np_00024 --num-funcs 2
