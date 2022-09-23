import inspect
import re
from abc import ABCMeta, abstractmethod
from copy import deepcopy
from typing import Callable, Dict, List, Union

from mitmproxy import http

from PCRoxyMode import PCRoxyMode
from tools.FlowUtils import adaptive_decode, adaptive_encode, get_active_part, is_pcr_api
from tools.PCRoxyLog import PCRoxyLog


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
    def __init__(self, core, data: Dict = {}) -> None:
        self.payload = data
        self._ctx_name: Union[None, str] = None
        self._ctx: Union[None, Dict] = None
        self.core = core

    # @property
    # def core(self) -> PCRoxy:
    #     return _PCRoxy_core

    @property
    def payload(self) -> Dict:
        return self._payload

    @payload.setter
    def payload(self, new_dict):
        self._payload = new_dict

    @property
    def ctx(self) -> Dict:
        if self._ctx is None:
            raise RuntimeError("Access context before load")
        return self._ctx

    @ctx.setter
    def ctx(self, new_dict):
        if self._ctx is None:
            raise RuntimeError("Access context before load")
        self._ctx = new_dict

    def load_ctx(self, fnode: FuncNode):
        if self._ctx_name is not None:
            self.store_ctx()
        self._ctx_name = fnode.plugin_name
        self._ctx = self.core.ctx_storage[self._ctx_name]

    def store_ctx(self):
        if self._ctx_name is None or self._ctx is None:
            return
        self.core.ctx_storage[self._ctx_name] = self._ctx
        self._ctx = None
        self._ctx_name = None

    def __del__(self):
        self.store_ctx()


class FlowChain:
    __metaclass__ = ABCMeta

    def __init__(self, core) -> None:
        self.chain: List[FuncNode] = []
        self.ready = False
        self.core = core

    def add_node(self, func_node: FuncNode):
        if self.ready is True:
            raise RuntimeWarning(f"Can't add {func_node} to a running chain.")
            return
        self.chain.append(func_node)

    def make_chain(self):
        self.chain.sort(reverse=True)
        self.ready = True

    @abstractmethod
    async def run_flow(self, flow: http.HTTPFlow, mode: PCRoxyMode):
        raise RuntimeError()


@PCRoxyLog
class HookChain(FlowChain):
    async def run_flow(self, flow: http.HTTPFlow, mode: PCRoxyMode):
        if not is_pcr_api(flow):
            return
        if not flow.marked:
            flow.marked = ':crown:'
        if not self.ready:
            raise RuntimeError("Chain was not ready!!!")
        origin_data = adaptive_decode(flow)
        context = HookCtx(self.core, deepcopy(origin_data))
        for node in self.chain:
            if mode not in node.mode_list:
                continue
            if re.match(node.path, flow.request.path) == None:
                continue
            self.logger(f'{node} handling {flow.request.path} '
                        f'{"request" if flow.response is None else "response"}', 'info')
            context.load_ctx(node)
            if node.is_async:
                await node.func(context=context)
            else:
                node.func(context=context)
        if mode == PCRoxyMode.MODIFIER and context.payload != origin_data:
            modified_raw = adaptive_encode(context.payload, flow)
            flow.marked = ':wrench:'
            get_active_part(flow).set_content(modified_raw)


@PCRoxyLog
class MockChain(FlowChain):
    async def run_flow(self, flow: http.HTTPFlow, mode: PCRoxyMode):
        if mode.isSafe() or not is_pcr_api(flow):
            return False
        if not self.ready:
            raise RuntimeError("Chain was not ready!!!")
        for node in self.chain:
            if re.match(node.path, flow.request.path) == None:
                continue
            self.logger(f'{node} mockup on {flow.request.path}', 'info')
            context = HookCtx(self.core, adaptive_decode(flow))
            context.load_ctx(node)
            mock_resp: http.Response
            if node.is_async:
                mock_resp = await node.func(context=context)
            else:
                mock_resp = node.func(context=context)
            flow.response = mock_resp
            flow.marked = ':ghost:'
            return True
        return False
