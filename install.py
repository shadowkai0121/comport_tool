import os
from tool import run_command
from update import update_all


def install_require() -> str:
    command = 'pip install -r requirement.txt'
    subprocess_obj = run_command(command)
    return command


if __name__ == '__main__':
    install_require()
    update_all()
