"""
Takes MFiX-Exa output from the tiny profiler and stores it in elasticsearch.
"""

import argparse
import datetime
import subprocess
import sys
import os

from elasticsearch_utils import get_elasticsearch_client

parser = argparse.ArgumentParser(description='Inputs for process class')
parser.add_argument('--es-index', dest='es_index', type=str, help='Elasticsearch index name')
parser.add_argument('--work-dir', dest='work_dir', type=str, help='Directory where data directories live')
parser.add_argument('--np', dest='np', type=str, help='length 4 string representing number of processes used')
parser.add_argument('--mfix-output-path', dest='mfix_output_data', type=str, help='Filepath of mfix timing data ${RUN_DATE}_${COMMIT_HASH}_${dir}')
parser.add_argument('--git-hash', dest='git_hash', type=str, help='Shortened mfix-exa git_hash (length 7)')
parser.add_argument('--git-branch', dest='git_branch', type=str, help='Shortened mfix-exa gitbranch (length 7)')
parser.add_argument('--sing-image-path', dest='sing_image_path', type=str, help='Singularity image path')
parser.add_argument('--type', dest='type', type=str, default=None, help='Special argument passed to exa (None, adapt)')
parser.add_argument('--validation-image-url', dest='validation_image_url', type=str, default=None, help='HCS validation image url')
parser.add_argument('--gas-fraction-image-url', dest='gas_fraction_image_url', type=str, default=None, help='Fluid bed gas-fraction validation image url')
parser.add_argument('--velocity-image-url', dest='velocity_image_url', type=str, default=None, help='Fluid bed velocity validation image url')
parser.add_argument('--video-url', dest='video_url', type=str, default=None, help='Validation paraview video')
args = parser.parse_args()


def get_input_filepaths(work_dir, np):
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

    return mfixdat_filepath, inputs_filepath


class MfixElasticsearchMessageBuilder:

    def __init__(self,
                 es_index,
                 mfix_output_filepath,
                 mfixdat_filepath,
                 inputs_filepath,
                 singularity_image_filepath,
                 validation_image_url=None,
                 gas_fraction_image_url=None,
                 velocity_image_url=None,
                 video_url=None):
        self.es_index = es_index
        self.mfix_output_filepath = mfix_output_filepath
        self.mfixdat_filepath = mfixdat_filepath
        self.inputs_filepath = inputs_filepath
        self.singularity_image_filepath = singularity_image_filepath
        self.validation_image_url = validation_image_url
        self.gas_fraction_image_url = gas_fraction_image_url
        self.velocity_image_url = velocity_image_url
        self.video_url = video_url
        self.function_list = ["calc_particle_collisions()",
            "des_time_loop()",
            "FabArray::ParallelCopy()",
            "FillBoundary_finish()",
            "FillBoundary_nowait()",
            "mfix_dem::EvolveParticles()",
            "mfix_dem::EvolveParticles_tstepadapt()",
            "mfix_dem::finderror()",
            "MLEBABecLap::Fsmooth()",
            "MLNodeLaplacian::Fsmooth()",
            "MLNodeLaplacian::prepareForSolve()",
            "MLNodeLaplacian::restriction()",
            "NeighborParticleContainer::buildNeighborList",
            "NeighborParticleContainer::getRcvCountsMPI",
            "NeighborParticleContainer::fillNeighborsMPI",
            "ParticleContainer::RedistributeMPI()"]
        self.message = {}
        self.elasticsearch_client = get_elasticsearch_client()

    def index_mfix_message(self):
        if not self.message:
            print("No mfix message built")
        else:
            res = self.elasticsearch_client.index(index=self.es_index, doc_type='_doc', body=self.message)
            print(res['result'])

    def build_mfix_elasticsearch_message(self):
        self.get_function_times_from_file(self.mfix_output_filepath)
        self.get_np(self.mfix_output_filepath)
        self.get_git_info()
        self.get_slurm_job_info()
        self.get_singularity_def_file_from_image(self.singularity_image_filepath)
        self.get_inputs_file(self.inputs_filepath)
        self.get_mfix_dat_file(self.mfixdat_filepath)

        # HCS validation image
        self.message['image_url'] = self.validation_image_url
        # Muller fluid bed validation images
        self.message['gas_fraction_image_url'] = self.gas_fraction_image_url
        self.message['velocity_image_url'] = self.velocity_image_url

        # Validation video
        self.message['video_url'] = self.video_url

    def get_inputs_file(self, filepath):
        with open(filepath, 'r') as file:
            self.message['inputs'] = file.read()

    def get_mfix_dat_file(self, filepath):
        try:
            with open(filepath, 'r') as file:
                self.message['mfix_dat'] = file.read()
        except FileNotFoundError:
            self.message['mfix_dat'] = ""

    def read_singularity_def_file(self, filepath):
        '''Stores the singularity definition file as a string'''
        with open(filepath, 'r') as file:
            self.message['singularity_def_file'] = file.read()

    def get_singularity_def_file_from_image(self, sing_image_path):
        '''Gets the Singularity definition file using
        singularity inspect and stores as a string'''
        self.message['singularity_def_file'] = subprocess.check_output(['singularity',
                                                    'inspect', '--deffile', sing_image_path]).decode("utf-8")

    def get_np(self, filename):
        #'/home/aaron/hcs_200k_ws/np_0001/2019-07-05_2437f2c_np_0001_adapt'
        #'/home/aaron/hcs_200k_ws/np_0001/2019-07-05_2437f2c_np_0001'

        if 'adapt' in filename:
            self.message['type'] = 'adapt'
            filename = filename[0:-(len(self.message['type'])+1)]
        elif 'morton' in filename:
            self.message['type'] = 'morton'
            filename = filename[0:-(len(self.message['type'])+1)]
        elif 'combined' in filename:
            self.message['type'] = 'combined'
            filename = filename[0:-(len(self.message['type'])+1)]
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


    def get_git_info(self):
        self.message['git_commit_time'] = subprocess.check_output(['singularity', 'exec',
                                        self.singularity_image_filepath, 'bash', '-c',
                                        "cd /app/mfix; git log -n 1 --pretty=format:'%at'"]).decode("utf-8")

        self.message['git_commit_hash'] = subprocess.check_output(['singularity', 'exec',
                                        self.singularity_image_filepath, 'bash', '-c',
                                        "cd /app/mfix; git log -n 1 --pretty=format:'%h'"]).decode("utf-8")

        self.message['git_branch'] = subprocess.check_output(['singularity', 'exec',
                                        self.singularity_image_filepath, 'bash', '-c',
                                        "cd /app/mfix; git rev-parse --abbrev-ref HEAD"]).decode("utf-8")


    def get_slurm_job_info(self):
        runtime = datetime.datetime.now()
        self.message['date'] = runtime.strftime("%Y-%m-%dT%H:%M:%SZ")

        self.message['job_nodes'] = os.environ['SLURM_NODELIST']
        self.message['jobnum'] = os.environ['SLURM_JOBID']
        self.message['modules'] = os.environ["LOADEDMODULES"]


# output_filepath, metadata_file = get_output_filenames(args.work_dir,
#         args.np, args.commit_date, args.git_hash, args.git_branch, args.type)

mfixdat_filepath, inputs_filepath = get_input_filepaths(args.work_dir, args.np)

builder = MfixElasticsearchMessageBuilder(args.es_index, args.mfix_output_data,
                        mfixdat_filepath, inputs_filepath, args.sing_image_path,
                        validation_image_url=args.validation_image_url,
                        gas_fraction_image_url=args.gas_fraction_image_url,
                        velocity_image_url=args.velocity_image_url,
                        video_url=args.video_url)
                        
builder.build_mfix_elasticsearch_message()
print(vars(builder))
builder.index_mfix_message()



## Index results into elasticsearch
# builder.index_mfix_message()

## Testing items
# print(args)
# python output_to_es.py --work-dir /home/aaron/hcs_200k_ws --np 0008 --commit-date 2019-07-05 \
# --git-hash 2437f2c --git-branch phase2-develop --sing-image-path /home/aaron/hcs_200k_ws/mfix-exa_phase2-develop_2437f2c.sif \
# --type adapt
# print(output_filepath, metadata_file, mfixdat_filepath, inputs_filepath, args.sing_image_path)

# for key, item in builder.message.items():
#     print(key, item)
