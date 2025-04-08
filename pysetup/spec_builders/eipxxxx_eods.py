from typing import Dict

from .base import BaseSpecBuilder
from ..constants import EIPXXXX_EODS


class EIPXXXX_EODSSpecBuilder(BaseSpecBuilder):
    fork: str = EIPXXXX_EODS
