from typing import Optional
from mitmproxy import contentviews, flow, http

from tools.BCRCryptor import BCRCryptor

class ViewBCRMsgPack(contentviews.msgpack.ViewMsgPack):
    name = "BCR msgpack"

    __content_types = (
        "application/msgpack",
        "application/x-msgpack",
        "application/octet-stream",
    )

    def __call__(
        self,
        data: bytes,
        *,
        content_type: Optional[str] = None,
        flow: Optional[flow.Flow] = None,
        http_message: Optional[http.Message] = None,
        **unknown_metadata,
    ) -> contentviews.TViewResult:
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
        if content_type not in self.__content_types:
            return 0
        if not flow.request.host.endswith('gzlj.bilibiligame.net'):
            return 0
        return 2