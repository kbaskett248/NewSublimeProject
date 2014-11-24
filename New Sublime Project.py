import errno
import logging
import os
import re
import subprocess

import sublime
import sublime_plugin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_template_paths():
    paths = {'Default': os.path.join(sublime.packages_path(),'New Sublime Project','Templates'),
             'User': os.path.join(sublime.packages_path(),'User','Sublime Project Templates')}
    logger.debug('Template paths: %s', paths)
    return paths

def get_env(environ_name):
    temp = os.getenv(environ_name)
    if (temp is None):
        if ('ProgramFiles' in environ_name) or ('ProgramW6432' in environ_name):
            temp = os.getenv('ProgramFiles')
    return temp

def get_program_path():
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

        if ((path is not None) and os.path.isdir(path)):
            for f in os.listdir(path):
                if (f.endswith('.exe') and ('sublime_text' in f)):
                    path = os.path.join(path, f)
                    break

        if ((path is None) or (not os.path.isfile(path))):
            path = 'sublime_text.exe'
    elif (plat == 'osx'):
        path = 'subl'
    elif (plat == 'linux'):
        pass

    return path

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

    yield project_root
    yield project_storage

def create_dir(dir):
    # Make the directory if it doesn't exist. If it does, just eat exception
    print("Creating dir " + dir)
    try:
        os.makedirs(dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


class NewSublimeProjectCommand(sublime_plugin.ApplicationCommand):
    disallowed_characters = {'\\':'-',
                             '/':'-',
                             ':':'-',
                             '*':'_',
                             '<':'_',
                             '>':'_',
                             '|':'_',
                             '*':'_',
                             '"':'_'}

    def run(self, type = None):
        self.type = type
        self.populate_vars()
        view = sublime.active_window().show_input_panel('Project Name', 
            "New Project", self.create_project, None, None)
        view.run_command('move_to', {'to': 'hardbol', 'extend': True})

    def populate_vars(self):
        self.vars = dict()
        self.vars['type'] = type
        self.vars['packages_path'] = sublime.packages_path().replace('\\', '/')

        self.populate_var_if_exist('program_files', 'ProgramFiles')
        self.populate_var_if_exist('program_files_x86', 'ProgramFiles(x86)')
        self.populate_var_if_exist('program_files_x64', 'ProgramW6432')

    def populate_var_if_exist(self, var_name, environ_name):
        temp = os.getenv(environ_name)
        if (temp != None):
            self.vars[var_name] = temp.replace('\\','/')
        elif ('ProgramFiles' in environ_name) or ('ProgramW6432' in environ_name):
            self.populate_var_if_exist(var_name, 'ProgramFiles')
        print (self.vars[var_name])

    def create_project(self, project_name):
        logger.info('Creating project: %s', project_name)
        self.workspace_file = None
        self.project_file = None
        self.project_name = project_name
        self.vars['project_name'] = project_name
        folder_name = NewSublimeProjectCommand.replace_disallowed_characters(project_name)
        self.vars['folder_name'] = folder_name

        project_root, project_storage = get_project_roots()
        self.vars['project_root'] = project_root.replace('\\', '/')
        self.project_folder = os.path.join(project_root,folder_name)
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
                sublime.status_message('Project folder already exists, but no project file found')
                self.open_project()
                print('Project folder already exists, but no project file found')
        else:
            self.get_templates()
            logger.debug('Templates: %s', self.templates)
            if self.type == None:
                sublime.active_window().show_quick_panel([x for x, y in self.templates], self.set_type)
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
                    self.workspace_file = os.path.join(root, f).replace('\\', '/')
                    break
                if '.sublime-project' in f:
                    self.project_file = os.path.join(root, f).replace('\\', '/')
                    break
            if (self.workspace_file is not None) or (self.project_file is not None):
                sublime.status_message('Project already exists; opening project')
                self.open_project()
                break

    @staticmethod
    def replace_disallowed_characters(path):
        for t,r in NewSublimeProjectCommand.disallowed_characters.items():
            path = path.replace(t,r)
        return path

    def get_templates(self):
        self.templates = list()
        for template_path in (x for x in get_template_paths().values() if os.path.isdir(x)):
            for d in os.listdir(template_path):
                path = os.path.join(template_path, d)
                if os.path.isdir(path):
                    self.templates.append((d, path))
            
    def set_type(self, type):
        if type != -1:
            self.type, self.template_folder = self.templates[type]
            self.vars['type'] = self.type
            self.vars['template_folder'] = self.template_folder.replace('\\', '/')
            self.copy_templates()

    def copy_templates(self):
        sublime.status_message('Creating and opening project')
        self.project_file = ""
        self.vars['project_file'] = self.project_file
        for root, dirs, files in os.walk(self.template_folder):
            suffix = root.replace(self.template_folder,'')
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
                    dest_folder = self.replace_vars(self.project_file_folder + suffix)
                    create_dir(dest_folder)
                    dest_file = self.replace_vars(os.path.join(dest_folder, tmp_file))
                    self.project_file = dest_file.replace('\\', '/')
                    self.vars['project_file'] = tmp_file
                elif '.sublime-workspace' in dest_file:
                    dest_folder = self.replace_vars(self.project_file_folder + suffix)
                    create_dir(dest_folder)
                    dest_file = self.replace_vars(os.path.join(dest_folder, tmp_file))
                    self.workspace_file = dest_file.replace('\\', '/')
                    self.vars['workspace_file'] = tmp_file
                self.copy_replace_files(os.path.join(tmp_source, f), dest_file)

        self.open_project()
        sublime.status_message('Creating and opening project')

    def open_project(self, project_path = None):
        file_to_open = None
        if (project_path is not None):
            file_to_open = project_path.replace('/', '\\')
        elif (self.workspace_file is not None):
            file_to_open = self.workspace_file.replace('/', '\\')
        elif (self.project_file is not None):
            file_to_open = self.project_file.replace('/', '\\')
        else:
            file_to_open = self.project_folder.replace('/', '\\')
        cmd = '{0} "{1}"'.format(get_program_path(), file_to_open)
        logger.debug(cmd)
        
        try:
            subprocess.Popen(cmd)
        except FileNotFoundError:
            logger.error('Could not launch %s', cmd)
            sublime.error_message('Failed to launch %s\n')
            open_folder(self.project_folder.replace('/', '\\'))

    def replace_vars(self, s):
        matches = re.findall('(\$\{([\w\._\d]+)\})', s)
        for m in matches:
            s = s.replace(m[0], self.vars[m[1]])
        return s

    def copy_replace_files(self, s, d):
        source = open(s, 'r')
        dest = open(d, 'w')
        for line in source:
            dest.write(self.replace_vars(line))
        dest.close()
        source.close()

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

    def run(self, user = False):
        paths = get_template_paths()
        if user:
            template_path = paths['User']
        else:
            template_path = paths['Default']

        create_dir(template_path)
        open_folder(template_path)
        
        