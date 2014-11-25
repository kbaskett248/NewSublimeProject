import errno
import logging
import os
import re
import shutil
import subprocess
from zipfile import ZipFile

import sublime
import sublime_plugin

import NewSublimeProject.src.new_sublime_project_api

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

ExecutablePath = None
TemplatePath = None
TemplatesToInstall = NewSublimeProject.src.new_sublime_project_api.TemplatesToInstall
DefaultVariables = NewSublimeProject.src.new_sublime_project_api.DefaultVariables
register_default_variable = NewSublimeProject.src.new_sublime_project_api.register_default_variable

DISALLOWED_CHARACTERS = {'\\': '-',
                         '/': '-',
                         ':': '-',
                         '*': '_',
                         '<': '_',
                         '>': '_',
                         '|': '_',
                         '*': '_',
                         '"': '_'}

TRANSFORM_UPPER = "U"
TRANSFORM_LOWER = "L"
TRANSFORM_HYPHEN = "-"
TRANSFORM_UNDERSCORE = "_"


def get_env(environ_name):
    temp = os.getenv(environ_name)
    if (temp is None):
        if (('ProgramFiles' in environ_name) or
                ('ProgramW6432' in environ_name)):
            temp = os.getenv('ProgramFiles')
    return temp


def replace_disallowed_characters(string):
    for t, r in DISALLOWED_CHARACTERS.items():
        string = string.replace(t, r)
    return string


def open_folder(path):
    if os.path.isdir(path):
        plat = sublime.platform()
        if (plat == 'windows'):
            subprocess.Popen(('explorer.exe', path))
        elif (plat == 'osx'):
            subprocess.Popen(('open', path))
        elif (plat == 'linux'):
            subprocess.Popen(('xdg-open', path))


def get_project_roots():
    settings = sublime.load_settings("New Sublime Project.sublime-settings")
    project_root = settings.get("project_root")
    if settings.get('use_separate_sublime_project_storage'):
        project_storage = settings.get('project_storage')
    else:
        project_storage = project_root

    return (project_root, project_storage)


def create_dir(dir_):
    # Make the directory if it doesn't exist. If it does, just eat exception
    try:
        os.makedirs(dir_)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    else:
        print("New Sublime Project: Creating directory " + dir_)


def plugin_loaded():
    global TemplatePath
    set_executable_path()
    setup_default_variables()
    TemplatePath = os.path.join(sublime.packages_path(),
                                'User',
                                'Sublime Project Templates')
    install_templates()


def set_executable_path():
    global ExecutablePath
    path = sublime.executable_path()
    if os.path.exists(path):
        ExecutablePath = path
        return
    else:
        path = None

    plat = sublime.platform()
    logger.debug('Platform = %s', plat)
    if (plat == 'windows'):
        version = sublime.version()[0]
        logger.debug('Version = %s', version)
        arch = sublime.arch()
        logger.debug('Architecture = %s', arch)

        folder = 'Sublime Text %s' % version

        if (arch == 'x32'):
            path = os.path.join(get_env('ProgramFiles'), folder)
        elif (arch == 'x64'):
            path = os.path.join(get_env('ProgramW6432'), folder)

        if (path is not None) and os.path.isdir(path):
            exe_path = os.path.join(path, 'subl.exe')
            if os.path.isfile(exe_path):
                path = exe_path
            else:
                exe_path = os.path.join(path, 'sublime_text.exe')
                if os.path.isfile(exe_path):
                    path = exe_path

        if ((path is None) or (not os.path.isfile(path))):
            path = 'sublime_text.exe'
    elif (plat == 'osx'):
        path = 'subl'
    elif (plat == 'linux'):
        path = 'subl'

    ExecutablePath = path


def setup_default_variables():
    def populate_var_if_exist(var_name, env_name):
        temp = get_env(env_name)
        if temp is not None:
            register_default_variable(var_name, temp.replace('\\', '/'))

    register_default_variable('packages_path',
                              sublime.packages_path().replace('\\', '/'))
    populate_var_if_exist('program_files', 'ProgramFiles')
    populate_var_if_exist('program_files_x86', 'ProgramFiles(x86)')
    populate_var_if_exist('program_files_x64', 'ProgramW6432')


def install_templates():
    possible_templates = sublime.find_resources('*.zip')
    for path, settings_file, setting in TemplatesToInstall:
        settings = sublime.load_settings(settings_file)
        if settings.get(setting, False):
            print('New Sublime Project: Installing templates from ' + path)
            for t in [x for x in possible_templates if x.startswith(path)]:
                zip_name = os.path.split(t)[1]
                template_name = os.path.splitext(zip_name)[0]

                # Delete template zip file if it exists
                zip_to = os.path.join(TemplatePath, zip_name)
                if os.path.exists(zip_to):
                    os.remove(zip_to)

                # Delete existing template folder if it exists
                template_path = os.path.join(TemplatePath, template_name)
                if os.path.isdir(template_path):
                    shutil.rmtree(template_path)

                # Copy template zip to templates folder
                zip_contents = sublime.load_binary_resource(t)
                with open(zip_to, 'wb') as zip_target:
                    zip_target.write(zip_contents)

                # Extract template zip to templates folder
                with ZipFile(zip_to) as zip_target:
                    zip_target.extractall(TemplatePath)

                # Delete template zip
                os.remove(zip_to)

            settings.set(setting, False)
            sublime.save_settings(settings_file)


class NewSublimeProjectCommand(sublime_plugin.ApplicationCommand):

    def run(self, type_=None):
        self.type = type_
        self.populate_vars()
        view = sublime.active_window().show_input_panel(
            'Project Name', "New Project", self.create_project, None, None)
        view.run_command('move_to', {'to': 'hardbol', 'extend': True})

    def populate_vars(self):
        global DefaultVariables
        self.vars = dict()
        self.vars.update(DefaultVariables)
        self.vars['type'] = self.type

    def get_var(self, k, transform=None):
        v = self.vars[k]
        if hasattr(v, '__call__'):
            v = v(*self.vars)

        if transform is None:
            return v

        if TRANSFORM_UPPER in transform:
            v = v.upper()
        elif TRANSFORM_LOWER in transform:
            v = v.lower()

        if TRANSFORM_HYPHEN in transform:
            v = v.replace(" ", "-")
        elif TRANSFORM_UNDERSCORE in transform:
            v = v.replace(" ", "_")

        return v

    def create_project(self, project_name):
        logger.info('Creating project: %s', project_name)
        self.workspace_file = None
        self.project_file = None
        self.project_name = project_name
        self.vars['project_name'] = project_name
        folder_name = replace_disallowed_characters(project_name)
        self.vars['folder_name'] = folder_name

        project_root, project_storage = get_project_roots()
        self.vars['project_root'] = project_root.replace('\\', '/')
        self.project_folder = os.path.join(project_root, folder_name)
        self.vars['project_folder'] = self.project_folder.replace('\\', '/')
        self.project_file_folder = os.path.join(project_storage, folder_name)

        if (os.path.isdir(self.project_folder)):
            logger.info('Project already exists; opening it.')
            # Open the project
            self.project_file = None
            self.workspace_file = None
            if (os.path.isdir(project_storage)):
                self.check_path_for_project(self.project_file_folder)
            if (self.project_file is None):
                self.check_path_for_project(self.project_folder)
            if (self.project_file is None):
                sublime.status_message(
                    'Project folder already exists, but no project file found')
                self.open_project()
                print(
                    'Project folder already exists, but no project file found')
        else:
            self.get_templates()
            logger.debug('Templates: %s', self.templates)
            if self.type is None:
                sublime.active_window().show_quick_panel(
                    [x for x, y in self.templates], self.set_type)
            elif self.type in [x for x, y in self.templates]:
                for x, y in self.templates:
                    if x == self.type:
                        self.template_folder = y
                        self.copy_templates()
                        break

    def check_path_for_project(self, path):
        for root, dirs, files in os.walk(path):
            for f in files:
                if '.sublime-workspace' in f:
                    self.workspace_file = os.path.join(root, f).replace(
                        '\\', '/')
                    break
                if '.sublime-project' in f:
                    self.project_file = os.path.join(root, f).replace(
                        '\\', '/')
                    break
            if ((self.workspace_file is not None) or
                    (self.project_file is not None)):
                sublime.status_message(
                    'Project already exists; opening project')
                self.open_project()
                break

    def get_templates(self):
        self.templates = list()
        for d in os.listdir(TemplatePath):
            path = os.path.join(TemplatePath, d)
            if os.path.isdir(path):
                self.templates.append((d, path))

    def set_type(self, type_):
        if type_ != -1:
            self.type, self.template_folder = self.templates[type_]
            self.vars['type'] = self.type
            self.vars['template_folder'] = self.template_folder.replace(
                '\\', '/')
            self.copy_templates()

    def copy_templates(self):
        sublime.status_message('Creating and opening project')
        self.project_file = ""
        self.vars['project_file'] = self.project_file
        for root, dirs, files in os.walk(self.template_folder):
            suffix = root.replace(self.template_folder, '')
            tmp_source = self.template_folder + suffix
            tmp_dest = self.project_folder + suffix
            create_dir(tmp_dest)

            for d in dirs:
                dest_folder = self.replace_vars(os.path.join(tmp_dest, d))
                create_dir(dest_folder)

            for f in files:
                tmp_file = self.replace_vars(f)
                dest_file = self.replace_vars(os.path.join(tmp_dest, tmp_file))
                if '.sublime-project' in dest_file:
                    dest_folder = self.replace_vars(
                        self.project_file_folder + suffix)
                    create_dir(dest_folder)
                    dest_file = self.replace_vars(
                        os.path.join(dest_folder, tmp_file))
                    self.project_file = dest_file.replace('\\', '/')
                    self.vars['project_file'] = tmp_file
                elif '.sublime-workspace' in dest_file:
                    dest_folder = self.replace_vars(
                        self.project_file_folder + suffix)
                    create_dir(dest_folder)
                    dest_file = self.replace_vars(
                        os.path.join(dest_folder, tmp_file))
                    self.workspace_file = dest_file.replace('\\', '/')
                    self.vars['workspace_file'] = tmp_file
                self.copy_replace_files(os.path.join(tmp_source, f), dest_file)

        self.open_project()
        sublime.status_message('Creating and opening project')

    def open_project(self, project_path=None):
        file_to_open = None
        if (project_path is not None):
            file_to_open = project_path.replace('/', '\\')
        elif (self.workspace_file is not None):
            file_to_open = self.workspace_file.replace('/', '\\')
        elif (self.project_file is not None):
            file_to_open = self.project_file.replace('/', '\\')
        else:
            file_to_open = self.project_folder.replace('/', '\\')
        cmd = '{0} "{1}"'.format(ExecutablePath, file_to_open)
        logger.debug(cmd)

        try:
            subprocess.Popen(cmd)
        except FileNotFoundError:
            logger.error('Could not launch %s', cmd)
            sublime.error_message('Failed to launch %s\n')
            open_folder(self.project_folder.replace('/', '\\'))

    def replace_vars(self, s):
        for m in re.findall(r"(\$\{([\w\._\d]+)(:[UL_\-]+)?\})", s):
            if m[2] is not None:
                t = m[2][1:]
            else:
                t = None
            s = s.replace(m[0], self.get_var(m[1], t))

        return s

    def copy_replace_files(self, s, d):
        with open(s, 'r') as source:
            with open(d, 'w') as dest:
                for line in source:
                    dest.write(self.replace_vars(line))


class ViewSublimeProjectsCommand(sublime_plugin.ApplicationCommand):

    def run(self):
        project_root, unused = get_project_roots()
        if os.path.isdir(project_root):
            open_folder(project_root.replace('/', '\\'))

    def is_enabled(self):
        result = False

        project_root, unused = get_project_roots()
        if os.path.isdir(project_root):
            result = True

        return result

    def is_visible(self):
        return self.is_enabled()


class ViewTemplatesCommand(sublime_plugin.ApplicationCommand):

    def run(self):
        create_dir(TemplatePath)
        open_folder(TemplatePath)
