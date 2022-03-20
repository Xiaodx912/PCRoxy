
from time import sleep
from typing import Optional
from mitmproxy import proxy, options, ctx, contentviews, flow, http
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.tools.web.master import WebMaster
from mitmproxy.addons import core
import threading
import asyncio

from PCRoxy import PCRoxy
from tools.ViewBCRMsgPack import ViewBCRMsgPack


class MitmWraper(object):
    mitm = None
    thread = None

    def loop_in_thread(self, loop, mitmdump):
        asyncio.set_event_loop(loop)
        mitmdump.run()

    def start(self, mode: str = 'dump'):
        mitm_dict = {'web': WebMaster, 'dump': DumpMaster}
        opts = options.Options(listen_host='0.0.0.0', listen_port=8012)
        self.mitm = mitm_dict[mode](opts)
        loop = asyncio.get_event_loop()
        self.thread = threading.Thread(
            target=self.loop_in_thread, args=(loop, self.mitm))
        self.thread.start()
        if mode == 'web':
            contentviews.add(ViewBCRMsgPack())


if __name__ == "__main__":
    mitm_wraper = MitmWraper()
    mitm_wraper.start('web')
    mitm_wraper.mitm.addons.add(PCRoxy(mitm_wraper.mitm))
    try:
        while(True):
            sleep(1)
    except KeyboardInterrupt:
        mitm_wraper.mitm.shutdown()
