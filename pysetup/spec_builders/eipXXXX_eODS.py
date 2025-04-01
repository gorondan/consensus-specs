from typing import Dict

from .base import BaseSpecBuilder
from ..constants import EIPXXXX_eODS


class EIPXXXX_eODSSpecBuilder(BaseSpecBuilder):
    fork: str = EIPXXXX_eODS
