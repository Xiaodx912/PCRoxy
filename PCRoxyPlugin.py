from functools import wraps
import os
import sys
from typing import Callable, Dict, List
from PCRoxy import _PCRoxy_core, FuncNode, PCRoxy, PCRoxyMode
from tools.PCRoxyLog import PCRoxyLog


def get_core() -> PCRoxy:
    if _PCRoxy_core is None:
        raise ValueError('No PCRoxy instance.')
    return _PCRoxy_core


@PCRoxyLog
class PCRoxyPlugin:
    def __init__(self, name: str = None, mode_list: List[PCRoxyMode] = []):
        back_filename = os.path.basename(
            sys._getframe().f_back.f_code.co_filename)
        self.logger(f'Loading plugin "{back_filename}"...', 'info')
        self.name = name if name is not None else back_filename.replace(
            '.py', '')
        self.config = self.core.config.get(self.name, {})
        self.mode = mode_list
        self.core.ctx_storage[self.name] = {}

    @property
    def core(self) -> PCRoxy:
        return get_core()

    def on_request(self, path: str, priority: int = 0) -> Callable:
        def req_hook_deco(func):
            @wraps(func)
            def wrapped_function(*args, **kwargs):
                return func(*args, **kwargs)
            node = FuncNode(func, self.name,
                            self.mode, path, priority)
            self.core.register_hook_function(node, 'request')
            return wrapped_function
        return req_hook_deco

    def on_response(self, path: str, priority: int = 0) -> Callable:
        def resp_hook_deco(func):
            @wraps(func)
            def wrapped_function(*args, **kwargs):
                return func(*args, **kwargs)
            node = FuncNode(func, self.name,
                            self.mode, path, priority)
            self.core.register_hook_function(node, 'response')
            return wrapped_function
        return resp_hook_deco

    def mock(self, path: str, priority: int = 0) -> Callable:
        def server_mock_deco(func):
            @wraps(func)
            def wrapped_function(*args, **kwargs):
                return func(*args, **kwargs)
            node = FuncNode(func, self.name,
                            self.mode, path, priority)
            self.core.register_hook_function(node, 'mock')
            return wrapped_function
        return server_mock_deco
