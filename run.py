
from colorama import Fore
import logging
from typing import Optional
from mitmproxy import proxy, options, ctx, contentviews, flow, http
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.tools.web.master import WebMaster
from mitmproxy.addons import core
import asyncio

from PCRoxy import PCRoxy
from tools.ViewBCRMsgPack import ViewBCRMsgPack


class MitmWraper(object):
    mitm = None

    async def start(self, mode: str = 'dump'):
        mitm_dict = {'web': WebMaster, 'dump': DumpMaster}
        opts = options.Options(listen_host='0.0.0.0', listen_port=8012)
        self.mitm = mitm_dict[mode](opts)
        self.mitm.options.update(termlog_verbosity='warn')
        self.mitm.addons.add(PCRoxy(self.mitm))
        if mode == 'web':
            contentviews.add(ViewBCRMsgPack())
        try:
            await self.mitm.run()
        except KeyboardInterrupt:
            self.mitm.shutdown()


if __name__ == "__main__":
    format = Fore.LIGHTCYAN_EX + \
        '┌ %(asctime)s - %(levelname)s [%(name)s] @%(filename)s:%(lineno)d \n└ ' + \
        Fore.RESET + '%(message)s'
    logging.basicConfig(format=format, datefmt='%H:%M:%S', level=logging.ERROR)

    mitm_wraper = MitmWraper()
    asyncio.run(mitm_wraper.start('web'))
