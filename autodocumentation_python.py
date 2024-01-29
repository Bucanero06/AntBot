import os
from difflib import get_close_matches

from shared.command_execution import execute_command
from shared.file_directory_ops import change_directory_manager, delete_files_or_directories, make_directory, copy_to, \
    validate_directory_and_get_full_path
from shared.logging import setup_logger

logger = setup_logger('autodocumentation_python')


def initialize_sphinx(source_dir, project_name, author_name, version='0.0.1'):
    # Run sphinx-quickstart automatically
    with change_directory_manager(source_dir):
        execute_command(f"sphinx-quickstart"
                        f" --quiet "
                        f"--project '{project_name}' "
                        f"--author '{author_name}' "
                        f"--language en "
                        f"-v {version} --release {version} "
                        f"--suffix .rst --master index --makefile --batchfile --sep --dot _"
                        )
        # subprocess.run(['sphinx-quickstart', '--quiet', '--project', str(project_name),  # '--author', str(author_name),
        #                 # '-v', str(version), '--release', str(version),
        #                 '--language', 'en', '--suffix', '.rst',
        #                 '--master', 'index', '--makefile', '--batchfile', '--sep', '--dot', '_'], cwd=source_dir)


def find_python_modules(start_path, ignore_folders=None):
    if ignore_folders is None:
        ignore_folders = []
    exclude_paths = [os.path.join(start_path, p) for p in ignore_folders]

    modules = []
    for root, dirs, files in os.walk(start_path):
        # Exclude the specified directories and their subdirectories
        dirs[:] = [d for d in dirs if os.path.join(root, d) not in exclude_paths]

        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                module_path = os.path.join(root, file)
                module_name = os.path.relpath(module_path, start_path).replace(os.path.sep, '.').rstrip('.py')
                modules.append(module_name)


    # Check that each path is real, for some reason some paths are missing letters from the end of the name
    modules_to_fix = []
    for module in modules:
        module_path = module.replace('.', os.path.sep) + '.py'
        if not os.path.exists(module_path):
            logger.warning(f'Failed to find module: {module}')
            modules_to_fix.append(module)

    # Search the path and find the closest match for the file name and switch it out
    for module_to_fix in modules_to_fix:
        base_path, module_file = os.path.split(module_to_fix.replace('.', os.path.sep))
        full_base_path = os.path.join(start_path, base_path)

        # Get list of files in the directory where the module should be
        try:
            files_in_dir = os.listdir(full_base_path)
        except FileNotFoundError:
            logger.error(f'Directory not found: {full_base_path}')
            continue

        # Find closest match to the expected module file name
        closest_matches = get_close_matches(module_file + '.py', files_in_dir, n=1, cutoff=0.6)

        if closest_matches:
            correct_module_file = closest_matches[0]
            correct_module_path = os.path.join(base_path, correct_module_file).replace(os.path.sep, '.').replace('.py', '')

            print(f'Found close match: {module_file} -> {correct_module_file} as module {correct_module_path}')
            index_in_modules = modules.index(module_to_fix)
            modules[index_in_modules] = correct_module_path # not replacing ...

        else:
            logger.error(f'No close match found for: {module_file} in {full_base_path}')

    if not modules:
        logger.error(f'Failed to find any modules in {start_path}')

    return modules


def update_conf_py(documentation_dir, source_dir):
    conf_py_path = os.path.join(documentation_dir, 'conf.py')
    source_conf_py_path = os.path.join(documentation_dir, 'source', 'conf.py')

    with open(source_conf_py_path, 'r') as file:
        lines = file.readlines()

    with open(conf_py_path, 'w') as f:
        f.write("import os\nimport sys\n")

        # write the lines
        for line in lines:
            f.write(line)

        f.write(f"sys.path.insert(0, os.path.abspath('{source_dir}'))\n")
        f.write("\nhtml_theme = 'sphinx_rtd_theme'\n")
        f.write("\nextensions = [\n")
        f.write("    'sphinx.ext.autodoc',\n"
                "    'sphinx.ext.doctest',\n"
                "    'sphinx.ext.intersphinx',\n"
                "    'sphinx.ext.todo',\n"
                "    'sphinx.ext.coverage',\n"
                "    'sphinx.ext.mathjax',\n"
                "    'sphinx.ext.ifconfig',\n"
                "    'sphinx.ext.viewcode',\n"
                "    'sphinx.ext.githubpages',\n"
                "    'sphinx.ext.napoleon',\n"
                "    'sphinx.ext.autosummary',\n"
                "    'sphinx.ext.autosectionlabel',\n"
                "    'sphinx.ext.autodoc.typehints',\n"
                "    'sphinx.ext.inheritance_diagram',\n"
                # "    'sphinx_click',\n"
                "]\n")
        f.write("\ntodo_include_todos = True\n")
    # Just in case copy the conf.py file to the source directory
    # subprocess.run(['cp', conf_py_path, source_conf_py_path])
    execute_command(f"cp {conf_py_path} {source_conf_py_path}")


def create_module_rst_files(modules, rst_dir):
    for module in modules:
        with open(os.path.join(rst_dir, f'{module}.rst'), 'w') as f:
            f.write(
                f"{module}\n{'=' * len(module)}\n\n"
                f".. automodule:: {module}\n"
                f"    :members:\n"
                f"    :undoc-members:\n"
                f"    :show-inheritance:\n\n"
                # f".. click:: {module}:cli_run\n"  # TODO: Fix this to be more general
                # f"    :prog: CLI for DensityPy\n"
                # f"    :nested: full\n\n"
                f".. inheritance-diagram:: {module}\n"
                f"    :parts: 1\n\n"
            )


def update_index_rst(documentation_dir, modules):
    index_rst_path = os.path.join(documentation_dir, 'index.rst')
    source_index_rst_path = os.path.join(documentation_dir, 'source/index.rst')
    with open(source_index_rst_path, 'r') as file:
        lines = file.readlines()

    with open(index_rst_path, 'w') as file:
        # Write descirption
        in_toctree = False
        for line in lines:
            if '.. toctree::' in line:
                in_toctree = True
                file.write(line)
                continue

            if in_toctree and line.strip() == ':caption: Contents:':
                file.write(line)
                file.write("\n")
                for module in sorted(set(modules)):  # Sort and remove duplicates
                    file.write(f"   {module}\n")
            elif in_toctree and not line.strip():
                # End of the toctree block
                in_toctree = False
                file.write(line)
            else:
                file.write(line)

    # Just in case copy the index.rst file to the source directory
    # subprocess.run(['cp', index_rst_path, source_index_rst_path])
    execute_command(f"cp {index_rst_path} {source_index_rst_path}")


def build_sphinx_docs(documentation_dir):
    # subprocess.run(['make', 'html'], cwd=documentation_dir)
    with change_directory_manager(documentation_dir):
        execute_command(f"make html")


def rename_files_and_replace_top_level_package_names(directory, top_level_package_name=None):
    logger.info(f'Renaming files and replacing top level package name in {directory}')

    targeted_remove = f'{top_level_package_name}.'
    # Walk through all files and folders within the directory
    for root, dirs, files in os.walk(directory):

        for file in files:
            file_path = os.path.join(root, file)

            check_to_replace_name = (file.endswith('.html') or file.endswith('.txt')
                                     or file.endswith('.js') or file.endswith('.rst'))
            check_to_replace_name = check_to_replace_name

            if check_to_replace_name:

                if file.startswith(targeted_remove):
                    new_file_name = file.replace(targeted_remove, '')
                    new_file_path = os.path.join(root, new_file_name)
                    os.rename(file_path, new_file_path)
                    file_path = new_file_path

                # Read the file and replace targeted_remove with ''
                with open(file_path, 'r') as f:
                    filedata = f.read()

                filedata = filedata.replace(targeted_remove, '')

                # Write the file out again
                with open(file_path, 'w') as f:
                    f.write(filedata)


def clean_up_and_exit(documentation_dir):
    try:
        delete_files_or_directories(f'{documentation_dir}_original', ignore_errors=True)
        execute_command(f"mv {documentation_dir} {documentation_dir}_original")
        make_directory(f'{documentation_dir}', delete_if_exists=True)  # New directory
        copy_to(f'{documentation_dir}_original/build/html/*', f'{documentation_dir}/', True)

    except Exception as e:
        logger.warning(f'Failed to clean up {documentation_dir}: {e}')
    finally:
        delete_files_or_directories(f'{documentation_dir}_original', ignore_errors=True)
        # Create an empty .nojekyll file to prevent GitHub Pages from ignoring files that begin with an underscore
        execute_command(f"touch {documentation_dir}/.nojekyll")
        logger.info(f'Finished creating documentation in {documentation_dir}')
        exit()


def main(project_name, author_name, source_dir, documentation_dir, exclude_dirs=None, remove_top_package_name=None,
         delete_old_files=False):
    source_dir = validate_directory_and_get_full_path(source_dir)
    documentation_dir = documentation_dir.strip()

    if not exclude_dirs:
        exclude_dirs = []

    if isinstance(exclude_dirs, str):
        exclude_dirs = exclude_dirs.split(',')
        exclude_dirs = [exclude_dir.strip() for exclude_dir in exclude_dirs]

    if delete_old_files and os.path.exists(documentation_dir):
        delete_files_or_directories(documentation_dir)

    if not os.path.exists(documentation_dir):
        os.makedirs(documentation_dir)

    documentation_dir = validate_directory_and_get_full_path(documentation_dir)

    initialize_sphinx(documentation_dir, project_name, author_name=author_name)
    modules = find_python_modules(source_dir, ignore_folders=exclude_dirs)
    update_conf_py(documentation_dir, source_dir)
    create_module_rst_files(modules, documentation_dir)
    update_index_rst(documentation_dir, modules)
    # Move the source files into the source directory
    execute_command(f"mv {documentation_dir}/*.rst {documentation_dir}/source/")
    build_sphinx_docs(documentation_dir)
    rename_files_and_replace_top_level_package_names(os.path.join(documentation_dir, 'build', 'html'),
                                                     top_level_package_name=remove_top_package_name)

    clean_up_and_exit(documentation_dir)


if __name__ == '__main__':
    import click


    @click.command()
    @click.option('--project_name', '-p', help='Name of the project', required=True)
    @click.option('--author_name', '-a', help='Name of the author', required=True)
    @click.option('--source_dir', '-s', help='Source directory', required=True)
    @click.option('--documentation_dir', '-d', help='Documentation directory', required=True)
    @click.option('--exclude_dirs', '-e', help='Directories to exclude', default=None)
    @click.option('--remove_top_package_name', '-t', help='Top level package names to remove', default=None)
    @click.option('--remove_old_files', '-r', is_flag=True, help='Remove old files', default=False)
    def main_cli(project_name, author_name, source_dir, documentation_dir, exclude_dirs, remove_top_package_name,
                 remove_old_files):
        main(project_name, author_name, source_dir, documentation_dir, exclude_dirs, remove_top_package_name,
             remove_old_files)


    main_cli()
