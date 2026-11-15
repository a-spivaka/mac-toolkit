#!/usr/bin/env python3
"""Generate an Automator Finder Quick Action that passes selected paths as argv."""
from pathlib import Path
import plistlib
import uuid

ROOT = Path(__file__).resolve().parent
CONTENTS = ROOT / 'Prepare Debug Bundle.workflow' / 'Contents'
CONTENTS.mkdir(parents=True, exist_ok=True)
name = 'Prepare Debug Bundle'
command = '"$HOME/.local/share/prepare-debug-bundle/run.sh" "$@"'
uuid_str = lambda: str(uuid.uuid4()).upper()

info = {
    'CFBundleIdentifier': 'dev.chizh.prepare-debug-bundle',
    'CFBundleName': name,
    'CFBundlePackageType': 'BNDL',
    'CFBundleVersion': '1.0',
    'NSServices': [{
        'NSMenuItem': {'default': name},
        'NSMessage': 'runWorkflowAsService',
        'NSSendFileTypes': ['public.item'],
        'NSRequiredContext': {'NSApplicationIdentifier': 'com.apple.finder'},
    }],
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
params = {
    'COMMAND_STRING': command,
    'CheckedForUserDefaultShell': True,
    'inputMethod': 1,  # Pass input as arguments, not stdin.
    'shell': '/bin/bash',
    'source': '',
}
action = {
    'AMAccepts': {'Container': 'List', 'Optional': True, 'Types': ['com.apple.cocoa.string']},
    'AMActionVersion': '2.0.3',
    'AMApplication': ['Automator'],
    'AMParameterProperties': {key: {} for key in params},
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
    'InputUUID': uuid_str(),
    'Keywords': ['Shell', 'Script', 'Command', 'Run', 'Unix'],
    'OutputUUID': uuid_str(),
    'UUID': uuid_str(),
    'UnlocalizedApplications': ['Automator'],
    'arguments': {
        str(index): {'default value': default, 'name': key, 'required': '0', 'type': '0', 'uuid': str(index)}
        for index, (key, default) in enumerate([
            ('inputMethod', 0), ('CheckedForUserDefaultShell', False),
            ('source', ''), ('COMMAND_STRING', ''), ('shell', '/bin/sh')
        ])
    },
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
for filename, data in (('Info.plist', info), ('document.wflow', workflow)):
    with (CONTENTS / filename).open('wb') as fd:
        plistlib.dump(data, fd, fmt=plistlib.FMT_XML, sort_keys=False)
print('Created', CONTENTS)
