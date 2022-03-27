import base64
import json
from typing import Dict, Union
from mitmproxy.http import HTTPFlow, Request, Response

from tools.BCRCryptor import BCRCryptor


def get_active_part(flow: HTTPFlow) -> Union[Request, Response]:
    return flow.request if flow.response is None else flow.response


def is_pcr_api(flow: HTTPFlow) -> bool:
    if not flow.request.host.endswith('gs-gzlj.bilibiligame.net'):
        return False
    if get_active_part(flow).headers.get('Content-Type', None) not in (
        "application/msgpack",
        "application/x-msgpack",
        "application/octet-stream",
    ):
        return False
    return True


def adaptive_decode(flow: HTTPFlow):
    raw = get_active_part(flow).raw_content
    if flow.request.query.get('format', '') == 'json':
        return json.loads(raw)
    else:
        return BCRCryptor().decrypt(raw)


def adaptive_encode(data: Dict, flow: HTTPFlow):
    if flow.request.query.get('format', '') == 'json':
        raw = json.dumps(data, separators=(',', ':')).encode()
    else:
        raw = BCRCryptor().encrypt(data, BCRCryptor().get_key(
            get_active_part(flow).raw_content))
        if flow.response is not None:
            raw = base64.b64encode(raw)
    return raw
