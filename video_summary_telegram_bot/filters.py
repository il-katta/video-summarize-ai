import re

from aiogram import filters

__all__ = ['AllCommands']


class AllCommands(filters.Command):
    def __init__(self):
        super().__init__(re.compile(r".*"))
