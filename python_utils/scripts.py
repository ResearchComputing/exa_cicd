""" Default configuration for slurm scripts """

class ScriptUtils:

    def __init__(self, commit_hash=None):
        self.mfix = "/app/mfix/build/mfix/mfix"
        self.base_working_dir = "/scratch/summit/holtat"
        self.prefix_image_path = "/scratch/summit/holtat/singularity/holtat-mfix_full:develop_"
        self.suffix_image_path = ".simg"
        self.image_commit_hash = commit_hash # 7 character hash, ex: 6b3f4ac
        self.mpirun = "/projects/holtat/spack/opt/spack/linux-rhel7-x86_64/gcc-6.1.0/openmpi-2.1.2-foemyxg2vl7b3l57e7vhgqtlwggubj3a/bin/mpirun"
        self.modules = ["singularity/2.5.2", "gcc/6.1.0"] # Lmod modules to load
        self.mpi_processes = None # np list to be handed to mpirun, ex: [1, 8, 27, 64]
        ## Slurm script options
        self.exclusive = True # Reserve full node?
        self.nodes = None # Number of nodes reserve
        self.account = "ucb1_summit2" # Slurm account to submit to
        self.time_limit = None # Max wall time

    def get_commit_date(self):
        """Get date of commit hash"""

        pass


    def verify_git_hash(self):
        """Check that input commit matches the commit has
        fromthe git repo in the container"""

        pass


    def create_metadata_file(self):
        """Create a metadata file with the commit hash, date, modules loaded,
        Slurm Nodelist, mfix 'inputs' file version, mfix 'mfix.dat' version,
        and mfix 'particle_input.dat' version. Each item should be on one line"""

        pass


    def run_mfix(self):
        """Run mfix exa, example command line command:
        $MPIRUN -np $np singularity exec $IMAGE bash -c "cd $WD/$dir; $MFIX inputs >> ${DATE}_${HASH}_${dir}" """

        pass


    def store_results(self):
        """Copy outputs from mfix exa run off of temporary scratch directory to
        a permanent storage location"""

        pass
