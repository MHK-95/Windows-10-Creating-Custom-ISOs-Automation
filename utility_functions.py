import sys
import os
import os.path as osp
import subprocess as sp
from typing import List, Callable
import itertools
import functools
import time

# Make flush=True the default behavior for print. When running this script inside a docker container, we want the
# output to print continuously to the terminal as the script goes, no all at the end.
print = functools.partial(print, flush=True)


def print_bold(message: str) -> None:
    print(f"\033[1m{message}\033[0m")


def print_err(message: str) -> None:
    print(f"\033[1;31m{message}\033[0m", file=sys.stderr)


def subprocess_error_handler(func: Callable):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sp.CalledProcessError as err:
            print_err("\nOops, a called system process didn't work. :^(")
            if err.stderr:
                stderr = err.stderr
                if isinstance(stderr, bytes):
                    stderr = stderr.decode()
                print(stderr, file=sys.stderr)
            raise

    return wrapper


# This type of function runs a subprocess and returns sp.CompletedProcess object.
SubprocessFunction = Callable[..., sp.CompletedProcess]
# This decorator will only work for functions that return a sp.CompletedProcess object.
def run_function_and_print_output(func: SubprocessFunction) -> SubprocessFunction:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> sp.CompletedProcess:
        cp = func(*args, **kwargs)
        stdout, stderr = cp.stdout, cp.stderr

        if stdout:
            if isinstance(stdout, bytes):
                stdout = stdout.decode()
            print(stdout)

        if stderr:
            if isinstance(stderr, bytes):
                stderr = stderr.decode()
            print(stderr, file=sys.stderr)

        return cp

    return wrapper


def check_environment() -> None:
    # Check the python version.
    if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 8) or \
            (sys.version_info.major == 3 and sys.version_info.minor == 8 and sys.version_info.micro < 1):
        print_err('\nThe python version needs to be 3.8.1 or greater.')
        sys.exit(1)

    # Check if run as root.
    if os.geteuid() != 0:
        print_err('\nThis python script can only be run as root.')
        sys.exit(1)

    # Check if the following programs are installed.
    program_list = ['mktemp', '7z', 'genisoimage', 'wimmountrw', 'wimunmount']
    for program in program_list:
        try:
            sp.run(['which', program], check=True, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
        except sp.CalledProcessError:
            print_err(f'\nThe program, {program}, is not installed.')
            sys.exit(1)


@run_function_and_print_output
@subprocess_error_handler
def ___run_cmd_check_verbose(cmd: List[str], verbose: bool) -> sp.CompletedProcess:
    if verbose:
        cmd.append('-v')
    return sp.run(cmd, check=True, stdout=sp.PIPE, stderr=sp.PIPE)


def copy_recursively(source_dir: str, dest_dir: str, verbose: bool = False) -> sp.CompletedProcess:
    return ___run_cmd_check_verbose(['cp', '-r', source_dir, dest_dir], verbose)


def copy_file(file_path: str, dest_file_path: str, verbose: bool = False) -> sp.CompletedProcess:
    return ___run_cmd_check_verbose(['cp', file_path, dest_file_path], verbose)


def rm_dir_recursively(dir: str, verbose: bool = False) -> sp.CompletedProcess:
    return ___run_cmd_check_verbose(['rm', '-r', '-f', dir], verbose)


def make_tmp_dir() -> str:
    cp = sp.run(['mktemp', '-d'], check=True, text=True, stdout=sp.PIPE, stderr=sp.PIPE)
    return cp.stdout.strip()


@run_function_and_print_output
@subprocess_error_handler
def extract_from_iso(dest_dir, iso_path: str = 'storage_dir/isos/baseline_win_10.iso') -> sp.CompletedProcess:
    return sp.run(['7z', 'x', '-y', f'-o{dest_dir}', iso_path], check=True, text=True, stdout=sp.PIPE, stderr=sp.PIPE)


@run_function_and_print_output
@subprocess_error_handler
def convert_dir_to_bootable_iso(iso_path: str, target_dir: str,
                                boot_path: str = osp.join('boot', 'etfsboot.com')) -> sp.CompletedProcess:
    cmd = ['genisoimage', '-no-emul-boot', '-boot-load-seg', '0x07C0', '-boot-load-size', '8', '-iso-level', '3',
           '-udf', '-joliet', '-D', '-N', '-relaxed-filenames', '-allow-limited-size', '-b', boot_path, '-o', iso_path,
           target_dir]

    # genisoimage sends its output to stderr and not stdout for some reason
    cp = sp.run(cmd, check=True, text=True, stdout=sp.PIPE, stderr=sp.PIPE)
    # Keep only the header and tail information
    stderr: List[str] = cp.stderr.splitlines()
    stderr = stderr[:7] + [''] + stderr[-6:]
    cp.stderr = str.join('\n', stderr)
    return cp


@run_function_and_print_output
@subprocess_error_handler
def wim_mount_rw(wim_path: str, mnt_dir: str, image_index: int = 1) -> sp.CompletedProcess:
    return sp.run(['wimmountrw', wim_path, str(image_index), mnt_dir], check=True, text=True, stdout=sp.PIPE,
                  stderr=sp.PIPE)


@run_function_and_print_output
@subprocess_error_handler
def wim_umount_dir(mnt_dir: str) -> sp.CompletedProcess:
    cp = sp.run(['wimunmount', mnt_dir, '--commit', '--force'], check=True, text=True, stdout=sp.PIPE, stderr=sp.PIPE)
    stdout = cp.stdout.splitlines()
    new_stdout = itertools.takewhile(lambda line: 'Using XPRESS compression with' not in line, stdout)
    cp.stdout = str.join('\n', new_stdout)
    # Sleep for 5 seconds or genisoimage might produce an error stating that the install.wim staging directory doesn't
    # exit. The filesystem needs time to update.
    time.sleep(5)
    return cp
