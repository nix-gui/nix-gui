import subprocess
import pylspclient
import threading


class ReadPipe(threading.Thread):
    def __init__(self, pipe):
        threading.Thread.__init__(self)
        self.pipe = pipe

    def run(self):
        line = self.pipe.readline().decode('utf-8')
        while line:
            print('pipe:', line)
            line = self.pipe.readline().decode('utf-8')


def get_language_server_client():
    print('aa')
    print(subprocess.run(['echo', '$RUST_LOG']).stdout)
    import pdb;pdb.set_trace()
    print('bb')
    cmd = ["rnix-lsp"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    read_pipe = ReadPipe(p.stderr)
    read_pipe.start()
    json_rpc_endpoint = pylspclient.JsonRpcEndpoint(p.stdin, p.stdout)

    lsp_endpoint = pylspclient.LspEndpoint(json_rpc_endpoint)

    lsp_client = pylspclient.LspClient(lsp_endpoint)
    root_uri = 'file:///etc/nixos/'
    workspace_folders = [{'name': 'python-lsp', 'uri': root_uri}]

    capabilities = {'completionProvider': {}, 'definitionProvider': True, 'documentLinkProvider': {'resolveProvider': False}, 'hoverProvider': True, 'textDocumentSync': {'change': 1, 'openClose': True}}

    lsp_client.initialize(p.pid, None, root_uri, None, capabilities, "off", workspace_folders)
    print('initialized:', lsp_client.initialized())


    file_path = "/etc/nixos/test.nix"
    uri = "file://" + file_path
    text = open(file_path, "r").read()
    languageId = "nix"#pylspclient.lsp_structs.LANGUAGE_IDENTIFIER.C
    version = 1
    lsp_client.didOpen(pylspclient.lsp_structs.TextDocumentItem(uri, languageId, version, text))


    lsp_client.definition(pylspclient.lsp_structs.TextDocumentIdentifier(uri), pylspclient.lsp_structs.Position(6, 4))

    lsp_client.shutdown()
    lsp_client.exit()


get_language_server_client()
