from argparse import Namespace
import argparse
import sys
import utility_functions as uf
import os.path as osp
import subprocess as sp
import traceback

this_dir = osp.dirname(osp.realpath(__file__))
windows_unattended_xml = osp.join(this_dir, 'autounattend-files', 'autounattend-mbr.xml')
first_login_scripts_dir = osp.join(this_dir, 'first-login-scripts')


def parse_args() -> Namespace:
    description = 'This program creates a modified Windows 10 ISO with files baked in the install.wim, and with an ' \
                  'autounnatend.xml file at the root of the ISO.'

    arg_parser = argparse.ArgumentParser(description=description, allow_abbrev=False)
    arg_parser.add_argument('a1', metavar='input_iso', type=str, help='The path to the input iso file.')
    arg_parser.add_argument('a2', metavar='output_iso', type=str, help='The path to the output iso file.')
    arg_parser.add_argument('-u', '--uefi', action='store_true', help='Make the Windows autounattend.xml boot from '
                                                                      'uefi instead of mbr.')

    args = arg_parser.parse_args()

    if not osp.isfile(args.a1):
        uf.print_err(f"The first argument, {args.a1}, does not exit.")
        sys.exit(1)

    output_iso_dir = osp.split(args.a2)[0]
    if not osp.isdir(output_iso_dir):
        uf.print_err(f"The second argument's directory, {args.a2}, does not exit.")
        sys.exit(1)

    if args.uefi:
        global windows_unattended_xml
        windows_unattended_xml = osp.join(this_dir, 'autounattend-files', 'autounattend-uefi.xml')

    return args


def main():
    args = parse_args()
    windows_iso, output_iso = args.a1, args.a2

    iso_dir, wim_dir, exit_code = None, None, 1

    try:
        uf.print_bold("Checking Environment.")
        uf.check_environment()

        uf.print_bold("\nExtracting ISO.")
        iso_dir = uf.make_tmp_dir()
        uf.extract_from_iso(iso_dir)

        uf.print_bold("\nMounting install.wim in read write mode.")
        wim_path = osp.join(iso_dir, 'sources', 'install.wim')
        wim_dir = uf.make_tmp_dir()
        uf.wim_mount_rw(wim_path, wim_dir)

        uf.print_bold("\nCopying files over to the mounted install.wim.")
        uf.print_bold("\nCopying first login scripts.")
        dest_dir = osp.join(wim_dir, 'Users', 'Public')
        uf.copy_recursively(first_login_scripts_dir, dest_dir, verbose=True)

        uf.print_bold("Copying Hello-World.txt.")
        source_file = osp.join('storage_dir', 'Hello-World.txt')
        dest_file = osp.join(wim_dir, 'Users', 'Public', 'Hello-world.txt')
        uf.copy_file(source_file, dest_file, verbose=True)

        uf.print_bold("\nUnmounting install.wim and keeping the changes.")
        uf.wim_umount_dir(wim_dir)

        uf.print_bold("\nCopying autounattend.xml to the ISO directory.")
        uf.copy_file(windows_unattended_xml, osp.join(iso_dir, 'autounattend.xml'), verbose=True)

        uf.print_bold("\nConverting the ISO directory back to a bootable Windows ISO.")
        uf.convert_dir_to_bootable_iso(output_iso, iso_dir)

        uf.print_bold("\nThe custom Windows ISO has been successfully made.")
        uf.print_bold(osp.abspath(output_iso))
        exit_code = 0

    except Exception as err:
        uf.print_err("\nOops, an exception occured. :^(")
        uf.print_err("Printing Stack Trace.")
        print(str.join('', traceback.format_exception(None, err, err.__traceback__)), flush=True, file=sys.stderr)

    finally:
        uf.print_bold("\nCleaning up.")
        if wim_dir:
            sp.run(['wimunmount', wim_dir], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
            uf.rm_dir_recursively(wim_dir)

        if iso_dir:
            uf.rm_dir_recursively(iso_dir)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
