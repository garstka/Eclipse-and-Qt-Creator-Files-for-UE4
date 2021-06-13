#!/usr/bin/env python3
"""
1. Drop in the same directory as sln and uproject

2. Double click or execute from the command line to generate:

Source/EclipsePathsAndSymbols.xml
Source/{project_name}.pro
Source/includes.pri
Source/defines.pri
"""

from pathlib import Path
import os
import xml.etree.ElementTree as ET
import re
import glob

# Templates
ECLIPSE_PATHS_AND_SYMBOLS_TEMPLATE = (r'''<?xml version="1.0" encoding="UTF-8"?>
<cdtprojectproperties>
<section name="org.eclipse.cdt.internal.ui.wizards.settingswizards.IncludePaths">
<language name="Assembly Source File">

</language>
<language name="C++ Source File">
{includepaths}

</language>
<language name="C Source File">

</language>
<language name="Object File">

</language>
</section>
<section name="org.eclipse.cdt.internal.ui.wizards.settingswizards.Macros">
<language name="Assembly Source File">

</language>
<language name="C++ Source File">
{definitions}

</language>
<language name="C Source File">

</language>
<language name="Object File">

</language>
</section>
</cdtprojectproperties>
''')

ECLIPSE_INCLUDE_PATH_TEMPLATE = '<includepath>{path}</includepath>'
ECLIPSE_DEFINITION_NO_KEY_TEMPLATE = '<macro><name>{key}</name><value/></macro>'
ECLIPSE_DEFINITION_WITH_KEY_TEMPLATE = '<macro><name>{key}</name><value>{value}</value></macro>'

# Template based on https://github.com/nibau/Unreal-Qt-project-generator
QT_PROJECT_PRO_TEMPLATE = r'''
TEMPLATE = app
CONFIG += console
CONFIG -= app_bundle
CONFIG -= qt
CONFIG += c++14

include(defines.pri)

{headers}

{sources}

include(includes.pri)
'''

QT_HEADER_LINE_TEMPLATE = r'HEADERS += "{path}"'
QT_SOURCE_LINE_TEMPLATE = r'SOURCES += "{path}"'
QT_DEFINES_PRI_LINE_WITH_VALUE_TEMPLATE = r'DEFINES += "{key}={value}"'
QT_DEFINES_PRI_LINE_NO_VALUE_TEMPLATE = r'DEFINES += "{key}"'
QT_INCLUDES_PRI_LINE_TEMPLATE = r'INCLUDEPATH += "{path}"'

# Working dir
WORKING_DIR = Path(__file__).parent.absolute()

# Input
SOLUTION_DIR = WORKING_DIR
PROJECT_NAME = glob.glob("*.sln")[0][:-4]
VCXPROJ_REFERENCE_PATH = WORKING_DIR / Path('Intermediate/Build')
VCXPROJ_PATH_GAME = (WORKING_DIR / Path(
    'Intermediate/ProjectFiles/{project_name}.vcxproj'.format(project_name=PROJECT_NAME))).absolute()
VCXPROJ_PATH_UE4 = (WORKING_DIR / Path('Intermediate/ProjectFiles/UE4.vcxproj')).absolute()
VCXPROJ_PATHS = [VCXPROJ_PATH_GAME,
                 VCXPROJ_PATH_UE4]

# Output
ECLIPSE_PATHS_AND_SYMBOLS_PATH = WORKING_DIR / Path("Source/EclipsePathsAndSymbols.xml")
QT_PROJECT_PRO_PATH = WORKING_DIR / Path("Source/{project_name}.pro".format(project_name=PROJECT_NAME))
QT_INCLUDES_PRI_PATH = WORKING_DIR / Path("Source/includes.pri")
QT_DEFINES_PRI_PATH = WORKING_DIR / Path("Source/defines.pri")

# Constants
VCXPROJ_INCLUDE_PATHS_DELIMITER = ';'
VCXPROJ_NAMESPACES = {'n': 'http://schemas.microsoft.com/developer/msbuild/2003'}

# Tweaks
ADDITIONAL_DEFINES = R'''
#define __INTELLISENSE__
'''

COMMON_INCLUDE_WITH_VARIADIC_MACROS = \
    Path(glob.glob(
        r'C:\Program Files\Epic Games\UE_4.*\Engine\Source\Runtime\CoreUObject\Public\UObject\ObjectMacros.h')[0])


def escape_text_for_xml(to_escape: str):
    escaped = to_escape.replace("&", "&amp;")
    escaped = escaped.replace("<", "&lt;")
    escaped = escaped.replace(">", "&gt;")
    escaped = escaped.replace("\"", "&quot;")
    return escaped


def escape_text_for_pri(to_escape: str):
    escaped = to_escape.replace(r'"', r'\"')
    return escaped


def replace_variables_in_includes(include_paths_text: str):
    include_paths_text = include_paths_text.replace("$(SolutionDir)", str(SOLUTION_DIR) + "\\")
    return include_paths_text


def parse_vcxproj(vcxproj_path: Path,
                  include_paths_list: list,
                  force_includes_list: list,
                  headers_list: list,
                  sources_list: list):
    tree = ET.parse(vcxproj_path)  # Project
    all_include_dirs_paths = tree.findall("./n:PropertyGroup/n:IncludePath", namespaces=VCXPROJ_NAMESPACES)
    all_include_dirs_paths.extend(
        tree.findall("./n:ItemGroup/n:ClCompile/n:AdditionalIncludeDirectories", namespaces=VCXPROJ_NAMESPACES))

    for include_paths in all_include_dirs_paths:
        if include_paths.text is not None:
            include_paths_text = include_paths.text
            include_paths_text = replace_variables_in_includes(include_paths_text)
            include_paths_list.extend([Path(path)
                                       for path
                                       in include_paths_text.split(VCXPROJ_INCLUDE_PATHS_DELIMITER)
                                       if path])

    all_force_include_files_paths = tree.findall("./n:ItemGroup/n:ClCompile/n:ForcedIncludeFiles",
                                                 namespaces=VCXPROJ_NAMESPACES)
    for include_paths in all_force_include_files_paths:
        if include_paths.text is not None:
            include_paths_text = include_paths.text
            include_paths_text = replace_variables_in_includes(include_paths_text)
            force_includes_list.extend([Path(path)
                                        for path
                                        in include_paths_text.split(VCXPROJ_INCLUDE_PATHS_DELIMITER)
                                        if path])

    # if vcxproj_path == VCXPROJ_PATH_UE4:  # Uncomment to skip UE headers and sources for Qt Creator
    #    return

    all_headers = tree.findall("./n:ItemGroup/n:ClInclude",
                               namespaces=VCXPROJ_NAMESPACES)

    for header in all_headers:
        if "Include" in header.attrib:
            header_path = header.attrib["Include"]
            headers_list.append(Path(header_path))

    all_sources = tree.findall("./n:ItemGroup/n:ClCompile",
                               namespaces=VCXPROJ_NAMESPACES)

    for source in all_sources:
        if "Include" in source.attrib:
            source_path = source.attrib["Include"]
            sources_list.append(Path(source_path))


def resolve_relative_paths(relative_paths_list):
    relative_paths_list_unique = list({path for path in relative_paths_list})
    os.chdir(VCXPROJ_REFERENCE_PATH)
    absolute_paths_list = [path.absolute() for path in relative_paths_list_unique]
    os.chdir(WORKING_DIR)

    return absolute_paths_list


def filter_dirs_and_report_missing(dirs_list):
    dirs = [path for path in dirs_list if path.is_dir()]
    not_dirs = [path for path in dirs_list if not path.is_dir()]

    for not_dir in not_dirs:
        print("Not a directory: {}".format(str(not_dir)))

    return dirs


def filter_files_and_report_missing(files_list):
    files = [path for path in files_list if path.is_file()]
    not_files = [path for path in files_list if not path.is_file()]

    for not_file in not_files:
        print("Not a file: {}".format(str(not_file)))

    return files


def generate_eclipse_include_path_tags(include_paths_list):
    include_paths_tags = [ECLIPSE_INCLUDE_PATH_TEMPLATE.format(path=str(path)) for path in include_paths_list]
    return include_paths_tags


def generate_qt_includes_list(include_paths_list):
    qt_includes_list = [QT_INCLUDES_PRI_LINE_TEMPLATE.format(path=str(path)) for path in include_paths_list]
    return qt_includes_list


def get_qt_definition_line(key, value):
    if value is None:
        return QT_DEFINES_PRI_LINE_NO_VALUE_TEMPLATE.format(key=key)
    return QT_DEFINES_PRI_LINE_WITH_VALUE_TEMPLATE.format(key=key, value=escape_text_for_pri(value))


def is_variadic_macro(key):
    return "(...)" in key  # Unsupported by Qt


def generate_qt_defines_list(definitions_map):
    qt_defines_list = [get_qt_definition_line(key, value) for key, value in definitions_map.items() if
                       not is_variadic_macro(key)]
    return qt_defines_list


def generate_qt_headers_list(headers_list):
    qt_headers_list = [QT_HEADER_LINE_TEMPLATE.format(path=str(path)) for path in headers_list]
    return qt_headers_list


def generate_qt_sources_list(sources_list):
    qt_sources_list = [QT_SOURCE_LINE_TEMPLATE.format(path=str(path)) for path in sources_list]
    return qt_sources_list


def update_definitions_from_string(definitions_map: dict, definitions_string: str):
    for line in definitions_string.splitlines():
        components = line.split(' ', maxsplit=2)  # [#define] [key] [optional value, assuming correct define]

        if len(components) < 2:
            continue

        directive = components[0]
        if directive != "#define":
            continue

        key = components[1]
        value = None if len(components) == 2 else components[2]
        definitions_map[key] = value


def update_definitions_with_variadic_macros(definitions_map):
    """Define variadic macros to nothing, this is a workaround for Eclipse being unable to handle includes
     in a sensible fashion"""
    pattern = re.compile("#define ([A-Z_]+\(\.\.\.\))")

    with open(COMMON_INCLUDE_WITH_VARIADIC_MACROS, 'r') as f:
        for match in re.findall(pattern, f.read()):
            definitions_map[match] = None


def get_definitions_map(force_includes_list):
    """Hoover up definitions from wherever we can"""
    definitions_map = {}
    for force_include_file in force_includes_list:
        with open(force_include_file, 'r') as f:
            update_definitions_from_string(definitions_map, f.read())
    update_definitions_from_string(definitions_map, ADDITIONAL_DEFINES)
    update_definitions_with_variadic_macros(definitions_map)

    return definitions_map


def get_eclipse_definition_tag(key, value):
    if value is None:
        return ECLIPSE_DEFINITION_NO_KEY_TEMPLATE.format(key=key)
    return ECLIPSE_DEFINITION_WITH_KEY_TEMPLATE.format(key=key, value=escape_text_for_xml(value))


def generate_eclipse_definitions_tags(definitions_map):
    definitions_tags = [get_eclipse_definition_tag(key, value) for key, value in definitions_map.items()]
    return definitions_tags


def parse_all_projects():
    include_paths_list = []
    force_includes_list = []
    headers_list = []
    sources_list = []
    for vcxproj_path in VCXPROJ_PATHS:
        assert (os.path.isfile(vcxproj_path))
        parse_vcxproj(vcxproj_path, include_paths_list, force_includes_list, headers_list, sources_list)

    return (filter_dirs_and_report_missing(resolve_relative_paths(include_paths_list)),
            filter_files_and_report_missing(resolve_relative_paths(force_includes_list)),
            filter_files_and_report_missing(resolve_relative_paths(headers_list)),
            filter_files_and_report_missing(resolve_relative_paths(sources_list)))


def main():
    os.chdir(WORKING_DIR)

    # Parse projects
    include_paths_list, force_includes_list, headers_list, sources_list = parse_all_projects()
    definitions_map = get_definitions_map(force_includes_list=force_includes_list)

    eclipse_include_paths_tags = generate_eclipse_include_path_tags(include_paths_list=include_paths_list)
    eclipse_definitions_tags = generate_eclipse_definitions_tags(definitions_map=definitions_map)
    eclipse_paths_and_symbols = ECLIPSE_PATHS_AND_SYMBOLS_TEMPLATE.format(
        includepaths='\n'.join(eclipse_include_paths_tags),
        definitions='\n'.join(eclipse_definitions_tags))

    qt_headers_list = generate_qt_headers_list(headers_list=headers_list)
    qt_sources_list = generate_qt_sources_list(sources_list=sources_list)
    qt_include_paths_list = generate_qt_includes_list(include_paths_list=include_paths_list)
    qt_defines_list = generate_qt_defines_list(definitions_map=definitions_map)
    qt_defines_pri = '\n'.join(qt_defines_list)
    qt_includes_pri = '\n'.join(qt_include_paths_list)
    qt_project_pro = QT_PROJECT_PRO_TEMPLATE.format(headers='\n'.join(qt_headers_list),
                                                    sources='\n'.join(qt_sources_list))

    with open(ECLIPSE_PATHS_AND_SYMBOLS_PATH, 'w') as f:
        print("Writing {}".format(ECLIPSE_PATHS_AND_SYMBOLS_PATH))
        f.write(eclipse_paths_and_symbols)

    with open(QT_DEFINES_PRI_PATH, 'w') as f:
        print("Writing {}".format(QT_DEFINES_PRI_PATH))
        f.write(qt_defines_pri)

    with open(QT_INCLUDES_PRI_PATH, 'w') as f:
        print("Writing {}".format(QT_INCLUDES_PRI_PATH))
        f.write(qt_includes_pri)

    with open(QT_PROJECT_PRO_PATH, 'w') as f:
        print("Writing {}".format(QT_PROJECT_PRO_PATH))
        f.write(qt_project_pro)

    print("Done")


if __name__ == '__main__':
    main()
