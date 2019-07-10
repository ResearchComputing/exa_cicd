"""
Takes MFiX-Exa output from the tiny profiler and stores it in elasticsearch.
"""

import datetime

from elasticsearch_utils import get_elasticsearch_client


get_elasticsearch_client()


class MfixElasticsearchMessageBuilder:

    def __init__(self):
        self.function_list = ["calc_particle_collisions()",
            "MLNodeLaplacian::Fsmooth()",
            "FillBoundary_nowait()",
            "NeighborParticleContainer::buildNeighborList",
            "mfix_dem::EvolveParticles_tstepadapt()"]

        self.message = {}

    def build_mfix_elasticsearch_message(self):
        mfix_output_filepath = '/home/aaron/hcs_200k_ws/np_0001/2019-07-05_2437f2c_np_0001'
        self.get_function_times_from_file(mfix_output_filepath)
        self.get_np(mfix_output_filepath)

        job_info_file = '/home/aaron/hcs_200k_ws/phase2-develop_2437f2c_info.txt'
        self.get_git_info(job_info_file)
        self.get_slurm_job_info(job_info_file)

        for key, val in self.message.items():
            print(key, val)

    def get_inputs_file(self, filepath):
        with open(filepath, 'r') as file:
            self.message['inputs'] = file.read()

    def get_mfix_dat(self, filepath):
        with open(filepath, 'r') as file:
            self.message['mfix_dat'] = file.read()

    def get_singularity_def_file(self, filepath):
        with open(filepath, 'r') as file:
            self.message['singularity_def_file'] = file.read()

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





builder = MfixElasticsearchMessageBuilder()
builder.build_mfix_elasticsearch_message()
