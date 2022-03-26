import asyncio
import base64
from collections import UserDict
import importlib
import inspect
import json
import os
import re

from typing import Any, Callable, Dict, KeysView, List, Mapping, Set, TypeVar, Union, ValuesView
from _collections_abc import dict_items, dict_keys, dict_values
from mitmproxy import ctx, http
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.tools.web.master import WebMaster
from enum import Enum

from tools.BCRCryptor import BCRCryptor


class PCRoxyMode(Enum):
    OBSERVER = 1
    MODIFIER = 2

    def isSafe(self) -> bool:
        return self in [PCRoxyMode.OBSERVER]


def PCRoxyLog(*args, **kwargs) -> Callable:
    def PCRoxy_insert_logger(cls):
        class PCRoxyLogger:
            def __init__(self):
                self.ctx = ctx
                self.cls_name = cls.__name__

            def __call__(self, msg: str, level: str = 'info') -> None:
                try:
                    log_func = self.ctx.log.__getattribute__(level)
                except AttributeError:
                    self.ctx.log.error(
                        f"[PCRoxyLogger] No such log level(log level: {level} )")
                log_func(self.format(msg))

            def format(self, msg: str) -> str:
                return f"[{self.cls_name}] {msg}"

        cls.logger = PCRoxyLogger()
        return cls
    if args and inspect.isclass(args[0]):
        return PCRoxy_insert_logger(args[0])
    return PCRoxy_insert_logger


class FuncNode:
    def __init__(self, func: Callable, plugin_name: str, mode_list: List[PCRoxyMode], path: str, priority: int) -> None:
        self.func = func
        self.plugin_name = plugin_name
        self.mode_list = mode_list
        self.path = path
        self.priority = priority
        self.is_async = inspect.iscoroutinefunction(func)

    def __lt__(self, other):
        return self.priority < other.priority

    def __str__(self) -> str:
        return f"{'async ' if self.is_async else ''}{self.plugin_name}::{self.func.__name__}"


class HookCtx:
    def __init__(self,) -> None:
        pass

    @property
    def payload(self) -> Dict:
        return self._payload

    @payload.setter
    def payload(self, new_dict):
        self._payload = new_dict


@PCRoxyLog()
class HookChain:
    __content_types = (
        "application/msgpack",
        "application/x-msgpack",
        "application/octet-stream",
    )

    def __init__(self) -> None:
        self.chain: List[FuncNode] = []
        self.ready = False

    def add_node(self, func_node: FuncNode):
        if self.ready is True:
            raise RuntimeWarning(f"Can't add {func_node} to a running chain.")
            return
        self.chain.append(func_node)

    def make_chain(self):
        self.chain.sort(reverse=True)
        self.cryptor = BCRCryptor()
        self.ready = True

    async def run_flow(self, flow: http.HTTPFlow, mode: PCRoxyMode):
        if not flow.request.host.endswith('gs-gzlj.bilibiligame.net'):
            return
        event = 'request' if flow.response is None else 'response'
        if flow.__getattribute__(event).headers.get('Content-Type', None) not in self.__content_types:
            return
        flow.marked = ':crown:'
        if not self.ready:
            raise RuntimeError("Chain was not ready!!!")
        context = HookCtx()
        raw = flow.__getattribute__(event).raw_content
        if flow.request.query.get('format', '') == 'json':
            context.payload = json.loads(raw)
        else:
            context.payload = self.cryptor.decrypt(raw)
        for node in self.chain:
            if mode not in node.mode_list:
                continue
            if re.match(node.path, flow.request.path) == None:
                continue
            self.logger(f'{node} handling {flow.request.path} {event}', 'info')
            if node.is_async:
                await node.func(context=context)
            else:
                node.func(context=context)
        if flow.request.query.get('format', '') == 'json':
            modified_raw = json.dumps(
                context.payload, separators=(',', ':')).encode()
        else:
            modified_raw = self.cryptor.encrypt(
                context.payload, self.cryptor.get_key(raw))
            if event == 'response':
                modified_raw = base64.b64encode(modified_raw)
        origin_data = json.loads(raw) if flow.request.query.get(
            'format', '') == 'json' else self.cryptor.decrypt(raw)
        if mode == PCRoxyMode.MODIFIER and context.payload != origin_data:
            print(f'Modify {flow.request.path} from\n'
                  f'{origin_data}\nto\n{context.payload}')
            flow.marked = ':wrench:'
            flow.__getattribute__(event).set_content(modified_raw)


_PCRoxy_core = None


@PCRoxyLog()
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
        self.hook_chain: Dict[str, HookChain] = {}
        self.hook_chain['request'] = HookChain()
        self.hook_chain['response'] = HookChain()
        _PCRoxy_core = self

    def load(self, loader):
        plugins = self.scan_plugins()
        for plugin in plugins:
            self.load_plugin(plugin)

    def running(self):
        for chain in self.hook_chain.values():
            chain.make_chain()

    async def request(self, flow: http.HTTPFlow):
        await self.hook_chain['request'].run_flow(flow, self.mode)

    async def response(self, flow: http.HTTPFlow):
        await self.hook_chain['response'].run_flow(flow, self.mode)

    def register_hook_function(self, func_node: FuncNode, chain_name: str):
        if chain_name not in self.hook_chain.keys():
            self.logger(f'Hook chain {chain_name} not found!', 'error')
            return
        self.hook_chain[chain_name].add_node(func_node)
        self.logger(
            f'Func {func_node} loaded by chain {chain_name}', 'info')

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
