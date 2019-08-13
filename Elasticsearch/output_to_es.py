"""
Takes MFiX-Exa output from the tiny profiler and stores it in elasticsearch.
"""

import datetime
import subprocess

from elasticsearch_utils import get_elasticsearch_client

# Variables I have in slurm script:
#{DATE} ${HASH} ${dir} {BRANCH} {COMMIT} {IMAGE}
#IMAGE=/scratch/summit/holtat/singularity/mfix-exa_${BRANCH}_${COMMIT}.sif
# Can get def file from "singularity inspect --deffile image_path"

def get_output_filenames(basedir, runtype, np, rundate, githash, gitbranch,
                            type, singularity_dir):
    '''Inputs:
    basedir: String base output directory filepath (ex: /scratch/summit/$USER)
    runtype: String directory name of the run (eg: hcs_200k_ws)
    np: 4 digit string representing number of processes used
    githash: shortened mfix-exa githash, string of length 7
    rundate: string of the rundate yyyy-mm-dd
    type: string of the special parameters used (ex: adapt)
    singularity_dir: string directory name where singularity images are found

    Returns the mfix output filepath, the metadata filepath, and the
    Singularity image filepath '''

    if not basedir[-1] == '/':
        basedir = basedir + '/'
    rundir = basedir + runtype + '/'
    output_filepath = rundir + np + '/' + rundate + '_' + \
                          githash + '_np_' + np
    if type:
        output_filepath += '_' + type

    metadata_filepath = rundir + gitbranch + '_' + githash + '_info.txt'

    singularity_image_filepath = singularity_dir + 'mfix-exa_' + gitbranch + \
                                 '_' + githash + '.sif'

    return output_filepath, metadata_file, singularity_image_file

def get_input_filepaths(basedir, runtype, np_list, type):
    '''Inputs:
    basedir: String base output directory filepath (ex: /scratch/summit/$USER)
    runtype: String directory name of the run (eg: hcs_200k_ws)
    np_list: list of 4 digit strings representing number of processes used
    type: string of the special parameters used (ex: adapt)
    Outputs:
    mfixdat_filepath: string
    inputs_filepath: string
    '''
    if not basedir[-1] == '/':
        basedir = basedir + '/'

    output_dir = basedir + runtype + '/' + np + '/'
    mfixdat_filepath = output_dir + 'mfix.dat'
    inputs_filepath = output_dir + 'inputs'

    if type:
        inputs_filepath += '_' + type

    return mfixdat_filepath, inputs_filepath



class MfixElasticsearchMessageBuilder:

    def __init__(self):
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
        mfix_output_filepath = '/home/aaron/hcs_200k_ws/np_0027/2019-07-05_2437f2c_np_0027_adapt'
        self.get_function_times_from_file(mfix_output_filepath)
        self.get_np(mfix_output_filepath)

        job_info_file = '/home/aaron/hcs_200k_ws/phase2-develop_2437f2c_info.txt'
        self.get_git_info(job_info_file)
        self.get_slurm_job_info(job_info_file)

        singularity_def_file = "/home/aaron/exa_cicd/def_files/mfix.def"
        self.get_singularity_def_file(singularity_def_file)

        inputs_file = "/home/aaron/hcs_200k_ws/np_0001/inputs"
        self.get_inputs_file(inputs_file)

        mfix_dat_file = "/home/aaron/hcs_200k_ws/np_0001/mfix.dat"
        self.get_mfix_dat_file(mfix_dat_file)

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


builder = MfixElasticsearchMessageBuilder()
builder.build_mfix_elasticsearch_message()
builder.index_mfix_message()
