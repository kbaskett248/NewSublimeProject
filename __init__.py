print('loading New Sublime Project __init__.py')

import NewSublimeProject.src.new_sublime_project_api


def register_template_folder_to_install(
        path, settings_file, setting='install_templates'):
    NewSublimeProject.src.new_sublime_project_api.register_template_folder_to_install(
        path, settings_file, setting)


def register_default_variable(var_name, var_value):
    NewSublimeProject.src.new_sublime_project_api.register_default_variable(
        var_name, var_value)


register_template_folder_to_install('Packages/NewSublimeProject/Templates',
                                    'New Sublime Project.sublime-settings')
