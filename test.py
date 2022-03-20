from mitmproxy import proxy, options
from mitmproxy.tools.web.master import WebMaster
import threading,asyncio

from mitmproxy import contentviews, http

class Rewrite:
    flag = 'default'

    @classmethod
    def set_flag(self, value):
        self.flag = value

    def load(self,loader):
        print('Load!')


    def request(self, flow):
        flow.request.headers['mitmproxy'] = self.flag


class MitmWebWraper(object):
    mitmweb = None
    thread = None

    def loop_in_thread(self, loop, mitmweb):
        asyncio.set_event_loop(loop)
        mitmweb.run()

    def start(self):
        opts = options.Options(listen_host='0.0.0.0', listen_port=8080,
                               confdir='~/.mitmproxy', ssl_insecure=True)
        #pconf = proxy.config.ProxyConfig(opts)
        self.mitmweb = WebMaster(opts)
        #self.mitmweb.server = proxy.server.ProxyServer(pconf)
        self.mitmweb.addons.add(Rewrite())
        loop = asyncio.get_event_loop()
        self.thread = threading.Thread(
            target=self.loop_in_thread, args=(loop, self.mitmweb))

        try:
            self.thread.start()
        except KeyboardInterrupt:
            self.mitmweb.shutdown()


if __name__ == "__main__":
    mitmweb_wraper = MitmWebWraper()
    mitmweb_wraper.start()