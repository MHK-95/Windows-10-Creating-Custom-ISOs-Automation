import subprocess as sp
from typing import List, Optional, Callable


def get_windows_username_by_id(user_id: int = 1) -> Optional[str]:
    """
    Will query the system and and return the username based on id.
    Will return None if no username was found.
    Can throw a CalledProcessError exception.
    """
    cp = sp.run(['query', 'user'], stdout=sp.PIPE, stderr=sp.DEVNULL, text=True)
    output: List[str] = cp.stdout.splitlines()

    # The following lambdas will split the spaces from the line and get the right column
    id: Callable[[str], str] = lambda line: line.split()[2]
    # the [1:] is to git rid of the extra '>' from the username
    username: Callable[[str], str] = lambda line: line.split()[0][1:]

    correct_line = next(filter(lambda line: id(line) == str(user_id), output), None)
    if correct_line:
        return username(correct_line)
    else:
        return None

