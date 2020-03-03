#!/bin/bash
#----------------------------------------------------------------------------------------------------------------------#
#                                                  docker-make-iso.sh                                                  #
#----------------------------------------------------------------------------------------------------------------------#

#------------------------------------------------------------------------------#
# EchoBold()                                                                   #
# Simply echos argument 1 as bold.                                             #
#------------------------------------------------------------------------------#
EchoBold() {
  echo -e "\033[1m$1\033[0m"
}

#------------------------------------------------------------------------------#
# Fail()                                                                       #
# Argument-$1: Error Message                                                   #
# Argument-$2: Exit Code                                                       #
# This function echos the error message to stderr in bold red and exits with   #
# the exit code.                                                               #
#------------------------------------------------------------------------------#
Fail() {
  msg="ERROR: $1 (code $2)"
  echo -e "\033[1;31m$msg\033[0m" 1>&2
  exit $2
}

#******************************************************************************#
#                    Validating Environment and User Input                     #
#******************************************************************************#
# Get the directory of this bash file rather than the current working directory.
dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# default values
docker_image_name="ubuntu_py_win_dep:18.04"
baseline_win_iso="./storage_dir/isos/baseline_win_10.iso"
custom_win_iso="./storage_dir/isos/custom_win_10.iso"

docker image inspect $docker_image_name \
  &>/dev/null || Fail "The required Docker image, $docker_image_name, is not setup on this machine." 1

# parse user options with getopts
while getopts ":hu" opt; do
  case $opt in
    \?)
      Fail "Unrecognized option" 1
      ;;
    h)
      h='-h'
      ;;
    u)
      u='-u'
      ;;
    esac
done
shift $((OPTIND -1))

if [ "$1" ]; then
  baseline_win_iso="$1"
fi

if [ "$2" ]; then
  custom_win_iso="$2"
fi

#******************************************************************************#
#                                 Main Script                                  #
#******************************************************************************#
EchoBold "\nStarting the docker container."
docker run --rm --privileged -i -v $dir:/work_dir $docker_image_name <<EOF
python /work_dir/main.py $h $u $baseline_win_iso $custom_win_iso
exit
EOF

