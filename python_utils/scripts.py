import os
import sys

class ScriptUtils:
    """Create functions and variables for code reuse in mfix exa slurm scripts"""

    def __init__(self,
            base_working_dir,
            commit_hash,
            np_list,
            nodes,
            results_dir,
            time_limit,
            account="ucb1_summit2",
            exclusive=True,
            image_prefix="/scratch/summit/holtat/singularity/holtat-mfix_full:develop_",
            image_suffix=".simg"
            job_name=None,
            mfix="/app/mfix/build/mfix/mfix",
            modules=["singularity/2.5.2", "gcc/6.1.0"],
            mpirun="/projects/holtat/spack/opt/spack/linux-rhel7-x86_64/gcc-6.1.0/openmpi-2.1.2-foemyxg2vl7b3l57e7vhgqtlwggubj3a/bin/mpirun",
            ):
        self.commit_hash = commit_hash # 7 character string, ex: 6b3f4ac
        self.mfix = mfix # mfix executable path
        self.base_working_dir = base_working_dir
        self.results_dir = results_dir # Where to copy results and metadata to
        self.metadata_dir = self.results_dir + "/metadata"
        ## Singularity image path = prefix+hash+suffix
        # ex: "/scratch/summit/holtat/singularity/holtat-mfix_full:develop_6b3f4ac.simg"
        self.image_prefix = image_prefix
        self.image_suffix = image_suffix
        self.image_path = self.image_prefix + self.commit_hash + self.image_suffix
        self.job_name = job_name
        self.mpirun = mpirun # mpirun executable
        self.modules = modules # Lmod modules to load
        self.np_list = np_list # np list to be handed to mpirun, ex: [1, 8, 27, 64]
        ## Slurm script options
        self.account = account # Slurm account to submit to
        self.exclusive = exclusive # Reserve full node?
        self.nodes = nodes # Number of nodes reserve
        self.time_limit = time_limit # Max wall time

    def write_batch_script(self):
        with open("submit.sh", 'wr') as batch_script:
            # SBATCH Directives
            batch_script.writeline("#!/bin/bash")
            batch_script.writeline("#SBATCH --account {account}".format(account=self.account))
            if self.exclusive:
                batch_script.writeline("#SBATCH --exclusive")
            batch_script.writeline("#SBATCH {nodes}".format(nodes=self.nodes))
            batch_script.writeline("#SBATCH {time_limit}".format(time_limit=self.time_limit))
            batch_script.writeline("#SBATCH {job_name}".format(job_name=self.job_name))

            # Run MFiX
            run_command = "python3 run_mfix.py --option run "
            run_command += "--commit-hash {commit_hash} ".format(commit_hash=self.commit_hash)
            run_command += "--results-dir {results_dir} ".format(results_dir=self.results_dir)
            run_command += "--working-dir {working_dir} ".format(working_dir=self.base_working_dir)
            run_command += "--mfix-exe {mfix} ".format(mfix=self.mfix)
            run_command += "--mpirun {mpirun}".format(mpirun=self.mpirun)
            batch_script.writeline(run_command)


    def run_script(self):
        """Check that variables make sense
        Store metadata
        Run mfix-exa
        Move results to permanent location"""
        self.verify_git_hash()
        self.create_metadata_file()
        self.mfix_command()
        self.store_results()

    def get_commit_date(self):
        """Get date of commit hash"""
        command = ['singularity', 'exec', self.image_path, 'bash', '-c', "cd /app/mfix; git log -n 1 --pretty=format:'%ai'"]
        date = subprocess.check_output(command)
        print(date)
        return date

    def get_slurm_nodelist(self):
        """Return a nodelist string consisting of node names from job
        example: 'shas[0102,0612,0852]'"""
        nodelist = os.getenv("SLURM_NODELIST")
        return nodelist

    def verify_git_hash(self):
        """Check that input commit matches the commit has
        fromthe git repo in the container"""
        command = ['singularity', 'exec', self.image_path, 'bash', '-c', "cd /app/mfix; git log -n 1 --pretty=format:'%h'"]
        git_hash = subprocess.check_output(command)
        print(git_hash, self.commit_hash)
        if git_hash == self.commit_hash:
            return True
        print("Input, Expected = " git_hash, self.commit_hash)
        sys.exit("Input git commit hash doesn't match container git hash")

    def create_metadata_file(self):
        """Create a metadata file with the commit hash, date, modules loaded,
        Slurm Nodelist, mfix 'inputs' file version, mfix 'mfix.dat' version,
        and mfix 'particle_input.dat' version. Each item should be on one line"""
        self.date = self.get_commit_date()
        nodelist = self.get_slurm_nodelist()
        modulenames = " ".join(self.modules)

        metadata_filename = self.metadata_dir + "/" + date + "_" + \
                                self.commit_hash + ".txt"
        with open(metadata_filename, "w") as metafile:
            metafile.write(self.date)
            metafile.write(self.commit_hash)
            metafile.write(nodelist)
            metafile.write(modulenames)


    def mfix_command(self):
        """Run mfix exa, example command line command:
        $MPIRUN -np $np singularity exec $IMAGE bash -c "cd $WD/$dir; $MFIX inputs >> ${DATE}_${HASH}_${dir}" """
        np_dir = self.get_np_dir()
        singularity_subcommand = """cd {wd}/{np_dir};
        {mfix} inputs >> {date}_{git_hash}_{np_dir}""".format(
                    wd=self.base_working_dir,
                    np_dir=np_dir,
                    mfix=self.mfix,
                    date=self.date,
                    git_hash=self.commit_hash
                    )
        command = [self.mpirun, self.np_list, 'singularity', 'exec', \
            self.image_path, 'bash', '-c', singularity_subcommand]
        subprocess.check_output(command)

    def get_np_dir(self, np):
        """Input: integer number of mpi processes
        Output: string representing output directory
        examples: 1 -> 'np_00001', 64 -> 'np_00064'"""
        directory = "np_" + str(np).zfill(5)
        return directory

    def store_results(self):
        """Copy outputs from mfix exa run off of temporary scratch directory to
        a permanent storage location"""

        pass
