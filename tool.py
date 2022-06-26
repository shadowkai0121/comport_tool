import subprocess


def run_command(command):
    print(f'Doing: {command}', flush=True)
    result = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8"
    )
    show_message(result)
    print(f'Done: {command}', flush=True)
    return result


def show_message(subprocess_obj):
    while True:
        line = subprocess_obj.stdout.readline()
        if not line:
            break
        print(line.rstrip(), flush=True)
