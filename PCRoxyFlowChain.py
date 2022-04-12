import inspect
import re
from abc import ABCMeta, abstractmethod
from copy import deepcopy
from typing import Callable, Dict, List

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
    def __init__(self, data: Dict = {}) -> None:
        self.payload = data

    @property
    def payload(self) -> Dict:
        return self._payload

    @payload.setter
    def payload(self, new_dict):
        self._payload = new_dict


class FlowChain:
    __metaclass__ = ABCMeta

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
        context = HookCtx(deepcopy(origin_data))
        for node in self.chain:
            if mode not in node.mode_list:
                continue
            if re.match(node.path, flow.request.path) == None:
                continue
            self.logger(f'{node} handling {flow.request.path} '
                        f'{"request" if flow.response is None else "response"}', 'info')
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
            context = HookCtx(adaptive_decode(flow))
            mock_resp: http.Response
            if node.is_async:
                mock_resp = await node.func(context=context)
            else:
                mock_resp = node.func(context=context)
            flow.response = mock_resp
            flow.marked = ':ghost:'
            return True
        return False
