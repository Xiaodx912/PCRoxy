import inspect
import logging
from colorama import Fore, Back

from typing import Callable

DEFAULT_COLOR_LUT = {
    'debug': f'{Fore.BLUE}{"{}"}{Fore.RESET}',
    'info': f'{Fore.WHITE}{"{}"}{Fore.RESET}',
    'warn': f'{Fore.YELLOW}{"{}"}{Fore.RESET}',
    'error': f'{Fore.RED}{"{}"}{Fore.RESET}',
    'critical': f'{Fore.RED+Back.WHITE}{"{}"}{Fore.RESET+Back.RESET}',
}


def PCRoxyLog(*args, **kwargs) -> Callable:
    def PCRoxy_insert_logger(cls):
        class PCRoxyLogger:
            __color_table = DEFAULT_COLOR_LUT

            def __init__(self):
                self.logger = logging.getLogger(cls.__name__)
                self.logger.setLevel(logging.DEBUG)

            def __call__(self, msg: str, level: str = 'info') -> None:
                level = level.lower()
                try:
                    log_func = self.logger.__getattribute__(level)
                    log_color = self.__color_table.__getitem__(level)
                except (AttributeError, KeyError):
                    logging.getLogger('PCRoxyLogger').error(self.__color_table['error'].format(
                        f"No such log level(log level: {level}) for log: {msg}"))
                    return
                log_func(log_color.format(msg), stacklevel=2)

        cls.logger = PCRoxyLogger()
        return cls
    if args and inspect.isclass(args[0]):
        return PCRoxy_insert_logger(args[0])
    return PCRoxy_insert_logger
