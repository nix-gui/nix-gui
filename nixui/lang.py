import subprocess
import pylspclient
import threading

import pyqt5  # test whether pyqt5 is imported


class ReadPipe(threading.Thread):
    def __init__(self, pipe):
        threading.Thread.__init__(self)
        self.pipe = pipe

    def run(self):
        line = self.pipe.readline().decode('utf-8')
        while line:
            print(line)
            line = self.pipe.readline().decode('utf-8')


def get_language_server_client():
    cmd = ["python", "-m", "nix-eval-lsp"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    read_pipe = ReadPipe(p.stderr)
    read_pipe.start()
    json_rpc_endpoint = pylspclient.JsonRpcEndpoint(p.stdin, p.stdout)

    lsp_endpoint = pylspclient.LspEndpoint(json_rpc_endpoint)

    lsp_client = pylspclient.LspClient(lsp_endpoint)
    capabilities = {
        'textDocument': {
            'codeAction': {'dynamicRegistration': True},
            'codeLens': {'dynamicRegistration': True},
            'colorProvider': {'dynamicRegistration': True},
            'completion': {
                'completionItem': {
                    'commitCharactersSupport': True,
                    'documentationFormat': ['markdown', 'plaintext'],
                    'snippetSupport': True
                },
                'completionItemKind': {'valueSet': list(range(1, 25 + 1))},
                'contextSupport': True,
                'dynamicRegistration': True
            },
            'definition': {'dynamicRegistration': True},
            'documentHighlight': {'dynamicRegistration': True},
            'documentLink': {'dynamicRegistration': True},
            'documentSymbol': {
                'dynamicRegistration': True,
                'symbolKind': {'valueSet': list(range(1, 26 + 1))}
            },
            'formatting': {'dynamicRegistration': True},
            'hover': {
                'contentFormat': ['markdown', 'plaintext'],
                'dynamicRegistration': True
            },
            'implementation': {'dynamicRegistration': True},
            'onTypeFormatting': {'dynamicRegistration': True},
            'publishDiagnostics': {'relatedInformation': True},
            'rangeFormatting': {'dynamicRegistration': True},
            'references': {'dynamicRegistration': True},
            'rename': {'dynamicRegistration': True},
            'signatureHelp': {
                'dynamicRegistration': True,
                'signatureInformation': {'documentationFormat': ['markdown', 'plaintext']}
            },
            'synchronization': {
                'didSave': True,
                'dynamicRegistration': True,
                'willSave': True,
                'willSaveWaitUntil': True
            },
            'typeDefinition': {'dynamicRegistration': True}
        },
        'workspace': {
            'applyEdit': True,
            'configuration': True,
            'didChangeConfiguration': {'dynamicRegistration': True},
            'didChangeWatchedFiles': {'dynamicRegistration': True},
            'executeCommand': {'dynamicRegistration': True},
            'symbol': {
                'dynamicRegistration': True,
                'symbolKind': {'valueSet': list(range(1, 26 + 1))}
            },
            'workspaceEdit': {'documentChanges': True},
            'workspaceFolders': True
        }
    }
    root_uri = 'file:///etc/nixos/'
    workspace_folders = [{'name': 'python-lsp', 'uri': root_uri}]
    print(lsp_client.initialize(p.pid, None, root_uri, None, capabilities, "off", workspace_folders))
    print(lsp_client.initialized())

    lsp_client.shutdown()
    lsp_client.exit()


get_language_server_client()
