import base64
from time import gmtime, strftime, time
from mitmproxy.http import Response

from PCRoxy import PCRoxyMode, HookCtx
from PCRoxyPlugin import PCRoxyPlugin
from tools.BCRCryptor import BCRCryptor

plugin = PCRoxyPlugin(mode_list=[PCRoxyMode.MODIFIER])

@plugin.mock(path='/clan_battle/top')
def mock_cbtop(context: HookCtx):
    h = {
        'Server': 'Tengine',
        'Content-Type': 'application/x-msgpack',
        'Transfer-Encoding': 'chunked',
        'Connection': 'keep-alive',
        'Date': strftime("%a, %d %b %Y %H:%M:%S GMT", gmtime()),
        'Timing-Allow-Origin': '*'
    }
    d = {
        'data_headers': {
            'short_udid': 0,
            'viewer_id': None,
            'sid': '',
            'servertime': int(time()),
            'result_code': 233
        },
        'data': {
            'server_error': {
                'status': 3,
                'title': '温馨小提示',
                'message': '阿伟，不要再打会战了。\\n去看一会书好不好？'
            }
        }
    }
    return Response.make(status_code=200,
                         content=base64.b64encode(BCRCryptor().encrypt(
                             d, BCRCryptor().gen_aes_key('server'))),
                         headers=h
                         )
