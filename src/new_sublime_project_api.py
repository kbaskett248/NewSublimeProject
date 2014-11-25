DefaultVariables = {}
TemplatesToInstall = []


def register_template_folder_to_install(
        path, settings_file, setting='install_templates'):
    global TemplatesToInstall
    TemplatesToInstall.append((path, settings_file, setting))


def register_default_variable(var_name, var_value):
    global DefaultVariables
    if isinstance(var_name, str):
        if (isinstance(var_value, str) or hasattr(var_value, '__call__')):
            DefaultVariables[var_name] = var_value
        else:
            DefaultVariables[var_name] = str(var_value)
