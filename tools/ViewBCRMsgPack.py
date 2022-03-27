import json
from typing import Optional
from mitmproxy import contentviews, flow, http

from tools.BCRCryptor import BCRCryptor
from tools.FlowUtils import is_pcr_api


class ViewBCRMsgPack(contentviews.msgpack.ViewMsgPack):
    name = "BCR msgpack"

    def __call__(
        self,
        data: bytes,
        *,
        content_type: Optional[str] = None,
        flow: Optional[flow.Flow] = None,
        http_message: Optional[http.Message] = None,
        **unknown_metadata,
    ) -> contentviews.TViewResult:
        if flow.request.query.get('format', '') == 'json':
            decrypted = json.loads(data)
            return f"BCR msgpack(json_plain)", contentviews.msgpack.format_msgpack(decrypted)
        else:
            decryptor = BCRCryptor()
            decrypted = decryptor.decrypt(data)
            return f"BCR msgpack(key={decryptor.get_key(data)})", contentviews.msgpack.format_msgpack(decrypted)

    def render_priority(
        self,
        data: bytes,
        *,
        content_type: Optional[str] = None,
        flow: Optional[flow.Flow] = None,
        http_message: Optional[http.Message] = None,
        **unknown_metadata,
    ) -> float:
        if is_pcr_api(flow):
            return 2
        return 0
