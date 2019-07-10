"""
Takes MFiX-Exa output from the tiny profiler and stores it in elasticsearch.
"""

from elasticsearch_utils import get_elasticsearch_client

get_elasticsearch_client()


class MfixElasticsearchMessageBuilder:

    self.function_list = ["calc_particle_collisions()",
        "MLNodeLaplacian::Fsmooth()",
        "FillBoundary_nowait()",
        "NeighborParticleContainer::buildNeighborList",
        "mfix_dem::EvolveParticles_tstepadapt()"]

    self.message = {}

    def build_mfix_elasticsearch_message():
        pass

    def get_inputs_file():
        self.message['inputs'] = ""

    def get_mfix_dat():
        self.message['mfix_dat'] = ""

    def get_singularity_def_file():
        self.message['singularity_def_file'] = ""

    def get_function_times():
        pass

    def get_wall_time():
        self.message['walltime'] = 0

    def get_git_info():
        self.message['git_commit_time'] = ""
        self.message['git_commit_hash'] = ""
        self.message['git_branch'] = ""

    def get_slurm_job_info():
        self.message['type'] = ""
        self.message['job_nodes'] = ""
        self.message['np'] = ""
        self.message['modules'] = ""
        self.message['date'] = ""
