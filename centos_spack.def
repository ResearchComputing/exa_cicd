BootStrap:docker
From:centos:centos7


%post

#yum check-update
#yum -y update
#yum -y upgrade

# Speed up yum
yum install -y yum-plugin-fastestmirror
yum install -y deltarpm

# Epel
yum install -y epel-release

# Omnipath and OpenMPI user libraries for Summit
yum install -y libhfi1 libpsm2 libpsm2-devel libpsm2-compat
yum install -y perftest qperf
yum install -y libibverbs libibverbs-devel rdma
yum install -y numactl-libs numactl-devel

# Environment modules
yum install -y Lmod
source /etc/profile.d/z00_lmod.sh

# Other useful libraries
yum install -y pciutils
yum install -y which

# Editors
yum install -y vim emacs

# GCC make bison flex etc
yum groupinstall -y 'Development Tools'
yum install -y wget

## SPACK install GCC, cmake, OpenMPI
# Define versions
#export gcc_ver=6.4.0
#export cmake_ver=3.10.1
#export openmpi_ver=2.1.0

# Environment for Spack/Mfix
mkdir -p /app
cd /app

useradd spack
chown -R spack:spack /app

# Install Spack
su - spack
whoami
cd /app
export gcc_ver=6.4.0
export cmake_ver=3.10.1
export openmpi_ver=2.1.0

git clone https://github.com/spack/spack.git
export SPACK_ROOT=/app/spack
export PATH=$SPACK_ROOT/bin:$PATH
spack bootstrap
source $SPACK_ROOT/share/spack/setup-env.sh

# Configure Spack Modules
cp -r $SPACK_ROOT/etc/spack/defaults/* $SPACK_ROOT/etc/spack/
sed -i '/prefix_inspections:/ i \ \ tcl: \
    hash_length: 0' $SPACK_ROOT/etc/spack/modules.yaml

# GCC
spack install gcc@$gcc_ver
module load gcc-$gcc_ver-gcc-4.8.5
spack compiler add
spack compiler find

# Cmake
spack install cmake@$cmake_ver %gcc@$gcc_ver
module load cmake-$cmake_ver-gcc-$gcc_ver

# OpenMPI with psm2 for Summit
spack install openmpi@$openmpi_ver %gcc@$gcc_ver fabrics=psm2,verbs thread_multiple=True

# Exit spack user
exit

# Edit command prompt so its short and shows you in a container
export PS1="Singularity > "



######################################################
%environment
export gcc_ver=6.4.0
export cmake_ver=3.10.1
export openmpi_ver=2.1.0

source /etc/profile
SPACK_ROOT=/app/spack
export SPACK_ROOT
source $SPACK_ROOT/share/spack/setup-env.sh
#module load bzip2-$bzip2_ver-gcc-4.8.5

module load cmake-$cmake_ver-gcc-$gcc_ver
module load gcc-$gcc_ver-gcc-4.8.5
module load openmpi-$openmpi_ver-gcc-$gcc_ver





#

