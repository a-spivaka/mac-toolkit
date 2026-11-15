#!/usr/bin/env python3
"""Build static macOS Automator Quick Action (Run Shell Script action).

Uses plistlib rather than hand-constructing XML so shell code and metadata stay valid.
"""
from pathlib import Path
import plistlib
import uuid

BASE = Path(__file__).resolve().parent
CONTENTS = BASE / 'Open Development Workspace.workflow' / 'Contents'
CONTENTS.mkdir(parents=True, exist_ok=True)

UUID = lambda: str(uuid.uuid4()).upper()
action_uuid = UUID()
name = 'Open Development Workspace'
command = '"$HOME/.local/share/open-dev-workspace/open-workspace.sh" "$@"'

info = {
    'CFBundleIdentifier': 'dev.chizh.open-development-workspace',
    'CFBundleName': name,
    'CFBundlePackageType': 'BNDL',
    'CFBundleVersion': '1.0',
    'NSServices': [
        {
            'NSMenuItem': {'default': name},
            'NSMessage': 'runWorkflowAsService',
            'NSSendFileTypes': ['public.folder'],
        }
    ],
}

metadata = {
    'applicationBundleID': 'com.apple.finder',
    'applicationBundleIDsByPath': {'/System/Library/CoreServices/Finder.app': 'com.apple.finder'},
    'applicationPath': '/System/Library/CoreServices/Finder.app',
    'applicationPaths': ['/System/Library/CoreServices/Finder.app'],
    'inputTypeIdentifier': 'com.apple.Automator.fileSystemObject',
    'outputTypeIdentifier': 'com.apple.Automator.nothing',
    'presentationMode': 15,
    'processesInput': 0,
    'serviceApplicationBundleID': 'com.apple.finder',
    'serviceApplicationPath': '/System/Library/CoreServices/Finder.app',
    'serviceInputTypeIdentifier': 'com.apple.Automator.fileSystemObject',
    'serviceOutputTypeIdentifier': 'com.apple.Automator.nothing',
    'serviceProcessesInput': 0,
    'systemImageName': 'NSActionTemplate',
    'useAutomaticInputType': 0,
    'workflowTypeIdentifier': 'com.apple.Automator.servicesMenu',
}

params = {'COMMAND_STRING': command, 'CheckedForUserDefaultShell': True,
          'inputMethod': 1, 'shell': '/bin/bash', 'source': ''}
parameter_props = {key: {} for key in params}
arguments = {}
for index, (key, default) in enumerate([
    ('inputMethod', 0), ('CheckedForUserDefaultShell', False),
    ('source', ''), ('COMMAND_STRING', ''), ('shell', '/bin/sh'),
]):
    arguments[str(index)] = {
        'default value': default, 'name': key, 'required': '0',
        'type': '0', 'uuid': str(index),
    }

action = {
    'AMAccepts': {'Container': 'List', 'Optional': True,
                  'Types': ['com.apple.cocoa.string']},
    'AMActionVersion': '2.0.3',
    'AMApplication': ['Automator'],
    'AMParameterProperties': parameter_props,
    'AMProvides': {'Container': 'List', 'Types': ['com.apple.cocoa.string']},
    'ActionBundlePath': '/System/Library/Automator/Run Shell Script.action',
    'ActionName': 'Run Shell Script',
    'ActionParameters': params,
    'BundleIdentifier': 'com.apple.RunShellScript',
    'CFBundleVersion': '2.0.3',
    'CanShowSelectedItemsWhenRun': False,
    'CanShowWhenRun': True,
    'Category': ['AMCategoryUtilities'],
    'Class Name': 'RunShellScriptAction',
    'InputUUID': UUID(),
    'Keywords': ['Shell', 'Script', 'Command', 'Run', 'Unix'],
    'OutputUUID': UUID(),
    'UUID': action_uuid,
    'UnlocalizedApplications': ['Automator'],
    'arguments': arguments,
    'isViewVisible': True,
    'location': '301.500000:375.000000',
    'nibPath': '/System/Library/Automator/Run Shell Script.action/Contents/Resources/Base.lproj/main.nib',
}
workflow = {
    'AMApplicationBuild': '523',
    'AMApplicationVersion': '2.10',
    'AMDocumentVersion': '2',
    'actions': [{'action': action, 'isViewVisible': True}],
    'connectors': {},
    'workflowMetaData': metadata,
}
with (CONTENTS / 'Info.plist').open('wb') as f:
    plistlib.dump(info, f, fmt=plistlib.FMT_XML, sort_keys=False)
with (CONTENTS / 'document.wflow').open('wb') as f:
    plistlib.dump(workflow, f, fmt=plistlib.FMT_XML, sort_keys=False)
print('Generated', CONTENTS)
