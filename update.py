import os
import re
from tool import run_command


def compile_file(input_path: str, ext: str, output_path: str, comipler) -> list:
    file_list = os.listdir(input_path)
    regex = re.compile(f'{ext}$')
    command_list = []
    for file in file_list:
        if regex.search(file):
            command_list.append(comipler(input_path, ext, output_path, file))
    return command_list


def ui_compiler(input_path: str, ext: str, output_path: str, file_name: str) -> str:
    py_file_name = file_name.replace(ext, '.py', 1)
    input_file = os.path.join(input_path, file_name)
    output_file = os.path.join(output_path, py_file_name)
    command = f'pyside6-uic {input_file} -o {output_file}'
    subprocess_obj = run_command(command)
    return command


def ts_compiler(input_path: str, ext: str, output_path: str, file_name: str) -> str:
    locale_list = ['us', 'tw']
    input_file = os.path.join(input_path, file_name)
    prefix = input_path.replace('/', '_')
    for locale in locale_list:
        ts_file_name = f'{prefix}_{file_name.rstrip(ext)}_{locale}.ts'
        output_file = os.path.join(output_path, ts_file_name)
        command = f'pyside6-lupdate {input_file} -ts {output_file}'
        subprocess_obj = run_command(command)
    return command


def qm_compiler(input_path: str, ext: str, output_path: str, file_name: str) -> str:
    ts_file_name = file_name.replace(ext, '.qm', 1)
    input_file = os.path.join(input_path, file_name)
    output_file = os.path.join(output_path, ts_file_name)
    command = f'pyside6-lrelease {input_file} -qm {output_file}'
    subprocess_obj = run_command(command)
    return command


def update_ui():
    ui_dir = 'ui'
    ui_ext = '.ui'
    output = 'ui_py'
    if not os.path.exists(output):
        os.mkdir(output)
    compile_file(ui_dir, ui_ext, output, ui_compiler)


def update_all():
    update_ui()


if __name__ == '__main__':
    update_all()
