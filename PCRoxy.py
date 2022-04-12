import importlib
import json
import os
import re
from enum import Enum
from typing import Dict, List, Union

from mitmproxy import http
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.tools.web.master import WebMaster

from PCRoxyFlowChain import FuncNode, HookChain, MockChain
from PCRoxyMode import PCRoxyMode
from tools.PCRoxyLog import PCRoxyLog

_PCRoxy_core = None


@PCRoxyLog
class PCRoxy:

    def __init__(self, dumpmaster: Union[DumpMaster, WebMaster]):
        global _PCRoxy_core
        try:
            self.config: Dict = json.load(
                open('./config.json', 'r', encoding='utf-8'))
        except:
            self.logger('Config not found!', 'warn')
            self.config = {}
        try:
            self.mode = PCRoxyMode.__getitem__(self.config['PCRoxy']['mode'])
        except KeyError:
            self.logger(
                'config.PCRoxy.mode error, fall back to OBSERVER mode', 'warn')
            self.mode = PCRoxyMode.OBSERVER
        self.mitmdump = dumpmaster
        self.logger(f'Starting in {self.mode.name} mode')
        if not self.mode.isSafe():
            self.logger(f'Dangerous mode!', 'warn')
        self.hook_chain: Dict[str, Union[HookChain, MockChain]] = {}
        self.hook_chain['request'] = HookChain()
        self.hook_chain['response'] = HookChain()
        self.hook_chain['mock'] = MockChain()
        _PCRoxy_core = self

    def load(self, loader):
        plugins = self.scan_plugins()
        for plugin in plugins:
            self.load_plugin(plugin)

    def running(self):
        for chain in self.hook_chain.values():
            chain.make_chain()

    async def request(self, flow: http.HTTPFlow):
        if await self.hook_chain['mock'].run_flow(flow, self.mode):
            return
        await self.hook_chain['request'].run_flow(flow, self.mode)

    async def response(self, flow: http.HTTPFlow):
        await self.hook_chain['response'].run_flow(flow, self.mode)

    def register_hook_function(self, func_node: FuncNode, chain_name: str):
        if chain_name in self.hook_chain.keys():
            self.hook_chain[chain_name].add_node(func_node)
            self.logger(
                f'Func {func_node} loaded by chain {chain_name}', 'info')
        else:
            self.logger(f'Hook chain {chain_name} not found!', 'error')
            return

    def scan_plugins(self, plugins_path: str = './plugins', module_prefix: str = 'plugins') -> List[str]:
        plugin_list = set()
        for name in os.listdir(plugins_path):
            path = os.path.join(plugins_path, name)
            if os.path.isfile(path) and \
                    (name.startswith('_') or not name.endswith('.py')):
                continue
            if os.path.isdir(path) and \
                (name.startswith('_') or not os.path.exists(
                    os.path.join(path, '__init__.py'))):
                continue
            m = re.match(r'([_A-Z0-9a-z]+)(.py)?', name)
            if not m:
                continue
            plugin_list.add(f'{module_prefix}.{m.group(1)}')
        return list(plugin_list)

    def load_plugin(self, module_path: str):
        importlib.import_module(module_path)
