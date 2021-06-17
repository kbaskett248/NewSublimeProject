# NewSublimeProject

A [Sublime Text 3](http://www.sublimetext.com/) package that makes it easy to create new projects and an accompanying directory populated with default files.


## Features

*   Quickly create and open a new project with folders and files already added.
*   Keep all projects in a single folder.
*   Define and customize templates consisting of folders and files.
*   Use variable substitution within folder names and file names and contents to create dynamic templates.
*   Other packages can include templates to install the first time they are loaded.


# Installation

## Package Control

Install [Package Control](http://wbond.net/sublime_packages/package_control). Add this repository (https://bitbucket.org/kbaskett/entityselect) to Package Control. EntitySelect will show up in the packages list.

## Manual installation

Go to the "Packages" directory (`Preferences` > `Browse Packages…`). Then download or clone this repository:

https://bitbucket.org/kbaskett/newsublimeproject.git


# Options

When editing settings, always make the changes to your user settings file (`Preferences` > `Package Settings` > `New Sublime Project` > `Settings - User`). Any changes to the package settings file will be overwritten when the package is updated.

*    *project_root*: the path to the folder where projects will be stored.
*    *use_separate_sublime_project_storage*: true to store \*.sublime-project and \*.sublime-workspace files to in a separate folder; false to store them in the project folder within *project_root*.
*    *project_storage*: the path to the folder where \*.sublime-project files and \*.sublime-workspace files will be stored if *use_separate_sublime_project_storage* is true.
*    *install_templates*: true to install templates bundled with New Sublime Project to the User Templates folder; false to prevent them from being installed. Note that this setting is automatically updated after templates are installed. It only needs to be changed to install the templates again.

## Example settings file

```javascript
{
    "project_root": "C:/Workspace",
    
    "use_separate_sublime_project_storage": false,
    
    "install_templates": false
}
```

