import argparse
from scripts import ScriptUtils, BatchTemplate

parser = argparse.ArgumentParser(description='Inputs for ScriptUtils')
## Required args
parser.add_argument('--commit-hash',
    dest='commit_hash',
    type=str,
    help='Git commit hash on mfix-exa develop branch',
    required=True)
parser.add_argument('--results-dir',
    dest='results_dir',
    type=str,
    help='Base directory to permanently store results',
    required=True)
parser.add_argument('--working-dir',
    dest='working_dir',
    type=str,
    help='High performance directory to initially output results to',
    required=True)
parser.add_argument('--np-list',
    dest='np_list',
    type=list,
    help='Run mfix exa with each np in np_list',
    required=True)
parser.add_argument('--nodes',
    dest='nodes',
    type=int,
    help='Number of nodes to run on',
    required=True)
parser.add_argument('--time-limit',
    dest='time_limit',
    type='int',
    help='Max walltime in hours',
    required=True)
## Optional args
parser.add_argument('--account',
    dest='account',
    default="ucb1_summit2",
    type=str,
    help='RMACC Summit Slurm account')
parser.add_argument('--mfix_exe',
    dest='mfix_exe',
    default="/app/mfix/build/mfix/mfix",
    type=str,
    help='Mfix-exa executable location within Singularity container')
parser.add_argument('--modules',
    dest='modules',
    type=list,
    default=["singularity/2.5.2"],
    help='Modules to load in batch script. List of strings.')
parser.add_argument('--mpirun',
    dest='mpirun',
    default="/projects/holtat/spack/opt/spack/linux-rhel7-x86_64/gcc-6.1.0/openmpi-2.1.2-foemyxg2vl7b3l57e7vhgqtlwggubj3a/bin/mpirun",
    type=str,
    help='Mpirun location on RMACC Summit (NOT one in container! Must be OpenMPI. Needs to match version in container)')

args = parser.parse_args()

script = ScriptUtils(
    base_working_dir=args.working_dir,
    commit_hash=args.commit_hash,
    np_list=args.np_list,
    nodes=args.nodes,
    results_dir=args.results_dir,
    time_limit=args.time_limit,
    account=args.account,
    exclusive=True,
    image_prefix="/scratch/summit/holtat/singularity/holtat-mfix_full:develop_",
    image_suffix=".simg"
    mfix=args.mfix_exe,
    modules=args.modules,
    mpirun=args.mpirun
)
