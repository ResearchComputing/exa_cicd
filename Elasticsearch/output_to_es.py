"""
Takes MFiX-Exa output from the tiny profiler and stores it in elasticsearch.
"""

import argparse
import datetime
import subprocess
import sys

from elasticsearch_utils import get_elasticsearch_client

parser = argparse.ArgumentParser(description='Inputs for process class')
parser.add_argument('--work-dir', dest='work_dir', type=str, help='Directory where data directories live')
parser.add_argument('--np', dest='np', type=str, help='length 4 string representing number of processes used')
parser.add_argument('--commit-date', dest='commit_date', type=str, help='Day of latest commit yyy-mm-dd')
parser.add_argument('--git-hash', dest='git_hash', type=str, help='Shortened mfix-exa git_hash (length 7)')
parser.add_argument('--git-branch', dest='git_branch', type=str, help='Shortened mfix-exa gitbranch (length 7)')
parser.add_argument('--image-path', dest='image_path', type=str, help='Singularity image path')
parser.add_argument('--type', dest='type', type=str, default=None, help='Special argument passed to exa (None, adapt)')
args = parser.parse_args()

def get_output_filenames(work_dir, np, commit_date, git_hash, git_branch, type):
    '''Inputs:
    work_dir: String base output directory filepath (ex: /scratch/summit/$USER/hcs_200k_ws)
    np: 4 digit string representing number of processes used
    git_hash: shortened mfix-exa githash, string of length 7
    commit_date: string of the commit_date yyyy-mm-dd
    type: string of the special parameters used (ex: adapt)
    singularity_image_path: string filepath where image is found
    Returns the mfix output filepath, the metadata filepath, and the
    Singularity image filepath '''

    if not work_dir[-1] == '/':
        work_dir = work_dir + '/'
    output_filepath = work_dir + 'np_' + np + '/' + commit_date + '_' + \
                          git_hash + '_np_' + np
    if type:
        output_filepath += '_' + type

    metadata_filepath = work_dir + git_branch + '_' + git_hash + '_info.txt'

    # singularity_image_filepath = singularity_dir + 'mfix-exa_' + git_branch + \
    #                              '_' + git_hash + '.sif'

    return output_filepath, metadata_filepath

def get_input_filepaths(work_dir, np, type):
    '''Inputs:
    work_dir: String base output directory filepath (ex: /scratch/summit/$USER/hcs_200k_ws)
    np: 4 digit string representing number of processes used
    type: string of the special parameters used (ex: adapt)
    Outputs:
    mfixdat_filepath: string
    inputs_filepath: string
    '''
    if not work_dir[-1] == '/':
        work_dir = work_dir + '/'

    output_dir = work_dir + 'np_' + np + '/'
    mfixdat_filepath = output_dir + 'mfix.dat'
    inputs_filepath = output_dir + 'inputs'

    if type:
        inputs_filepath += '_' + type

    return mfixdat_filepath, inputs_filepath


class MfixElasticsearchMessageBuilder:

    def __init__(self,
                 mfix_output_filepath,
                 metadata_filepath,
                 mfixdat_filepath,
                 inputs_filepath,
                 singularity_image_filepath):
        self.mfix_output_filepath = mfix_output_filepath
        self.metadata_filepath = metadata_filepath
        self.mfixdat_filepath = mfixdat_filepath
        self.inputs_filepath = inputs_filepath
        self.singularity_image_filepath = singularity_image_filepath
        self.function_list = ["calc_particle_collisions()",
            "MLNodeLaplacian::Fsmooth()",
            "FillBoundary_nowait()",
            "NeighborParticleContainer::buildNeighborList",
            "mfix_dem::finderror()",
            "NeighborParticleContainer::getRcvCountsMPI",
            "FillBoundary_finish()",
            "des_time_loop()",
            "mfix_dem::EvolveParticles()",
            "NeighborParticleContainer::fillNeighborsMPI",
            "ParticleContainer::RedistributeMPI()",
            "mfix_dem::EvolveParticles_tstepadapt()",]
        self.message = {}
        self.elasticsearch_client = get_elasticsearch_client()

    def index_mfix_message(self):
        if not self.message:
            print("No mfix message built")
        else:
            res = self.elasticsearch_client.index(index="mfix-hcs-200k", doc_type='_doc', body=self.message)
            print(res['result'])

    def build_mfix_elasticsearch_message(self):
        self.get_function_times_from_file(self.mfix_output_filepath)
        self.get_np(self.mfix_output_filepath)
        self.get_git_info(self.metadata_filepath)
        self.get_slurm_job_info(self.metadata_filepath)
        self.get_singularity_def_file_from_image(self.singularity_image_filepath)
        self.get_inputs_file(self.inputs_filepath)
        self.get_mfix_dat_file(self.mfixdat_filepath)

    def get_inputs_file(self, filepath):
        with open(filepath, 'r') as file:
            self.message['inputs'] = file.read()

    def get_mfix_dat_file(self, filepath):
        with open(filepath, 'r') as file:
            self.message['mfix_dat'] = file.read()

    def read_singularity_def_file(self, filepath):
        '''Stores the singularity definition file as a string'''
        with open(filepath, 'r') as file:
            self.message['singularity_def_file'] = file.read()

    def get_singularity_def_file_from_image(self, image_path):
        '''Gets the Singularity definition file using
        singularity inspect and stores as a string'''
        self.message['singularity_def_file'] = subprocess.check_output(['singularity',
                                                        'inspect', '--deffile', image_path])

    def get_np(self, filename):
        #'/home/aaron/hcs_200k_ws/np_0001/2019-07-05_2437f2c_np_0001_adapt'
        #'/home/aaron/hcs_200k_ws/np_0001/2019-07-05_2437f2c_np_0001'

        if 'adapt' in filename:
            self.message['type'] = 'adapt'
            filename = filename[0:-6]
        else:
            self.message['type'] = 'normal'

        self.message['np'] = int(filename.split('_')[-1])

    def get_function_times_from_file(self, filepath):
        with open(filepath, 'r') as file:
            tiny_profile_output = file.readlines()

            look_for_data = False
            for jj, line in enumerate(tiny_profile_output):

                tiny_profile_output[jj] = line.replace(", ", "_")

                if 'time spent in main ' in line.lower():
                    self.message['walltime'] = float(line.split()[-1])

                # Start individual function timing data
                if 'name' in line.lower() and '-----' in tiny_profile_output[jj + 1]:
                    look_for_data = True

                if look_for_data:
                    for function in self.function_list:
                        if function in line:
                            self.message[function] = float(line.split()[3])

                # End individual function timing data
                if '---------' in tiny_profile_output[jj] and 'incl.' in tiny_profile_output[jj + 3].lower():
                    look_for_data = False
                    break


    def get_git_info(self, job_info_filepath):
        #'/home/aaron/hcs_200k_ws/phase2-develop_2437f2c_info.txt'
        with open(job_info_filepath, 'r') as file:
            job_info = file.readlines()

            for jj, line in enumerate(job_info):
                if jj==0:
                    self.message['git_commit_time'] = line.split(' ')[0] + \
                                            "T" + line.split(' ')[1] + "Z"
                elif jj==1:
                    self.message['git_commit_hash'] = line.strip()
                elif jj==2:
                    self.message['job_nodes'] = line.strip()
                elif jj==3:
                    self.message['jobnum'] = line.strip()
                elif jj==5:
                    self.message['modules'] = line.strip()

    def get_slurm_job_info(self, filename):
        #'/home/aaron/hcs_200k_ws/phase2-develop_2437f2c_info.txt'
        job_info_file = filename.split('/')
        job_info = job_info_file[-1].split('_')
        self.message['git_branch'] = job_info[-3]

        runtime = datetime.datetime.now()
        self.message['date'] = runtime.strftime("%Y-%m-%dT%H:%M:%SZ")


output_filepath, metadata_file = get_output_filenames(args.work_dir,
        args.np, args.commit_date, args.git_hash, args.git_branch, args.type)

mfixdat_filepath, inputs_filepath = get_input_filepaths(args.work_dir, args.np, args.type)

builder = MfixElasticsearchMessageBuilder(output_filepath, metadata_file,
                            mfixdat_filepath, inputs_filepath, args.image_path)
builder.build_mfix_elasticsearch_message()
# print(builder.message)

with open('/scratch/summit/holtat/elastic_debug', 'w') as f:
    for key, item in builder.message.items():
        f.write(key, item)
## Index results into elasticsearch
# builder.index_mfix_message()

## Testing items
# print(args)
# python output_to_es.py --work-dir /home/aaron/hcs_200k_ws --np 0008 --commit-date 2019-07-05 \
# --git-hash 2437f2c --git-branch phase2-develop --image-path /home/aaron/hcs_200k_ws/mfix-exa_phase2-develop_2437f2c.sif \
# --type adapt
# print(output_filepath, metadata_file, mfixdat_filepath, inputs_filepath, args.image_path)
