# Adding-Files-To-Windows-10-ISOs
This repo contains a python script, main.py, that automates loading loading files into Windows ISOs.
This script was made by me and used by my corporation inside a continous deployment pipeline. 
Latest sofware from the git repo was loaded into these Windows ISOs in daily builds to be given to clients.
This repo will only load a Hello-World.txt file and an autounattend.xml to demonstrate a proof of concept.

## The Process
1. Extract a Windows 10 iso with 7z to a directory.
2. Mount the install.wim file on a directory with wimtools.
3. Copy over the files you want to the mounted install.wim.
4. Unmount the install.wim and commit the changes you made.
5. Copy over an autounattend.xml to the root of the iso directory.
5. Convert the files you extracted with 7z back to a bootable iso with mkisofs.
Now you have a custom Windows 10 iso with the files you want loaded on and an autounattend.xml.

## The Setup
This script was meant to run on a linux system, with Python 3.8.1 or higher, wimtools, mkisofs, and 7z.
Since there are quite a few dependencies, I made a Dockerfile for debian 10, that will have all the needed dependencies.

The Docker image is meant to be only built once online and then be run inside an offline environment.
The make_custom_windows_iso.sh bash script will run this docker image and create a custom-windows-10.iso in the storage/isos directory.
Currently, main.py is hardcoded to use storage/isos/windows-10-baseline.iso as the windows iso to modify.

The resources, like the isos, autoanttend.xml, and files to be copied over are stored in the storage_dir directory.
This directory constantly changes and is being ignored in .gitignore.


## Running the scripts
