#!/usr/bin/env python3
"""Generate self-contained macOS Automator Quick Action bundles for image-toolkit."""
import plistlib
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parent
ACTIONS = {
    'Image - Convert to JPEG': ('jpeg', 'dev.chizh.image-toolkit.jpeg'),
    'Image - Convert to PNG': ('png', 'dev.chizh.image-toolkit.png'),
    'Image - Resize to 1600px': ('resize1600', 'dev.chizh.image-toolkit.resize1600'),
    'Image - Web JPEG 1600px': ('web1600', 'dev.chizh.image-toolkit.web1600'),
}


def generate(name, mode, identifier):
    contents = BASE / f'{name}.workflow' / 'Contents'
    contents.mkdir(parents=True, exist_ok=True)
    command = f'"$HOME/.local/share/image-toolkit/image-toolkit.sh" {mode} "$@"'
    info = {
        'CFBundleIdentifier': identifier, 'CFBundleName': name,
        'CFBundlePackageType': 'BNDL', 'CFBundleVersion': '1.0',
        'NSServices': [{'NSMenuItem': {'default': name},
                        'NSMessage': 'runWorkflowAsService',
                        'NSSendFileTypes': ['public.image'],
                        'NSRequiredContext': {'NSApplicationIdentifier': 'com.apple.finder'}}],
    }
    metadata = {
        'applicationBundleID': 'com.apple.finder',
        'applicationBundleIDsByPath': {'/System/Library/CoreServices/Finder.app': 'com.apple.finder'},
        'applicationPath': '/System/Library/CoreServices/Finder.app',
        'applicationPaths': ['/System/Library/CoreServices/Finder.app'],
        'inputTypeIdentifier': 'com.apple.Automator.fileSystemObject',
        'outputTypeIdentifier': 'com.apple.Automator.nothing',
        'presentationMode': 15, 'processesInput': 0,
        'serviceApplicationBundleID': 'com.apple.finder',
        'serviceApplicationPath': '/System/Library/CoreServices/Finder.app',
        'serviceInputTypeIdentifier': 'com.apple.Automator.fileSystemObject',
        'serviceOutputTypeIdentifier': 'com.apple.Automator.nothing',
        'serviceProcessesInput': 0, 'systemImageName': 'NSActionTemplate',
        'useAutomaticInputType': 0,
        'workflowTypeIdentifier': 'com.apple.Automator.servicesMenu',
    }
    params = {'COMMAND_STRING': command, 'CheckedForUserDefaultShell': True,
              'inputMethod': 1, 'shell': '/bin/bash', 'source': ''}
    action = {
        'AMAccepts': {'Container': 'List', 'Optional': True,
                      'Types': ['com.apple.cocoa.string']},
        'AMActionVersion': '2.0.3', 'AMApplication': ['Automator'],
        'AMParameterProperties': {key: {} for key in params},
        'AMProvides': {'Container': 'List', 'Types': ['com.apple.cocoa.string']},
        'ActionBundlePath': '/System/Library/Automator/Run Shell Script.action',
        'ActionName': 'Run Shell Script', 'ActionParameters': params,
        'BundleIdentifier': 'com.apple.RunShellScript', 'CFBundleVersion': '2.0.3',
        'CanShowSelectedItemsWhenRun': False, 'CanShowWhenRun': True,
        'Category': ['AMCategoryUtilities'], 'Class Name': 'RunShellScriptAction',
        'InputUUID': str(uuid.uuid4()).upper(),
        'Keywords': ['Shell', 'Script', 'Command', 'Run', 'Unix'],
        'OutputUUID': str(uuid.uuid4()).upper(),
        'UUID': str(uuid.uuid4()).upper(),
        'UnlocalizedApplications': ['Automator'],
        'arguments': {
            str(index): {'default value': default, 'name': key, 'required': '0',
                         'type': '0', 'uuid': str(index)}
            for index, (key, default) in enumerate([
                ('inputMethod', 0), ('CheckedForUserDefaultShell', False),
                ('source', ''), ('COMMAND_STRING', ''), ('shell', '/bin/sh')])
        },
        'isViewVisible': True, 'location': '301.500000:375.000000',
        'nibPath': '/System/Library/Automator/Run Shell Script.action/Contents/Resources/Base.lproj/main.nib',
    }
    document = {'AMApplicationBuild': '523', 'AMApplicationVersion': '2.10',
                'AMDocumentVersion': '2', 'actions': [{'action': action, 'isViewVisible': True}],
                'connectors': {}, 'workflowMetaData': metadata}
    for filename, payload in [('Info.plist', info), ('document.wflow', document)]:
        with (contents / filename).open('wb') as f:
            plistlib.dump(payload, f, fmt=plistlib.FMT_XML, sort_keys=False)


for display_name, (mode, identifier) in ACTIONS.items():
    generate(display_name, mode, identifier)
print('Generated', len(ACTIONS), 'image workflows')
