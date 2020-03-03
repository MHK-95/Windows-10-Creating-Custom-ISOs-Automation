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
windows_iso="./storage_dir/isos/custom_win_10.iso"
docker_image_name="ubuntu_py_win_dep:18.04"

docker image inspect $docker_image_name \
  &>/dev/null || Fail "The required Docker image, $docker_image_name, is not setup on this machine." 1

if [ "$1" ]; then
  windows_iso="$1"
fi

#******************************************************************************#
#                                 Main Script                                  #
#******************************************************************************#
usb_device="/dev/$(lsblk -So NAME,TRAN | grep 'usb' | head -n 1 | awk '{print $1}')"
echo "$usb_device" | grep -q "/dev/sd." || Fail "Could not find a USB storage device on this computer." 1

EchoBold "Found USB device, $usb_device. Will make the USB into a Windows installer."
fdisk -l $usb_device

usb_partitions=$[ $(fdisk -l $usb_device | wc -l) - 8 ]
EchoBold "\nUmouting the USB."
for ((i=1; i<=$usb_partitions; i++)); do
  umount "${usb_device}${i}" 2> /dev/null
done

EchoBold "\nStarting the docker container."
docker run --privileged --rm -i -v $dir:/work_dir --device=$usb_device $docker_image_name <<EOF
woeusb --target-filesystem ntfs  --no-color --device "$windows_iso" $usb_device
exit
EOF
