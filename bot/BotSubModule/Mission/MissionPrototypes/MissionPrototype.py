from sc2.bot_ai import BotAI, Race
from sc2.data import Race, Difficulty
from sc2.player import Bot, Computer
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from sc2.ids.unit_typeid import UnitTypeId
from sc2.constants import *
from sc2.ids.ability_id import AbilityId
from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.ids.buff_id import BuffId
import asyncio


class MissionPrototype:
    # See StrategyDesignData for more information
    id: str
    layer: int
    # a unit can have multi missions at the same time, mission of larger layer will be execute
    piority: int
    # if there are multi missions of the same layer, larger piority mission will overwrite smaller one
    units: Units

    negativeOverallFactor: float = 1
    positiveOverallFactor: float = 1

    startCondition: str = ""
    endCondition: str = ""
    goalDesc: str = ""
    negativeDesc: str = ""  # may do more this mission
    positiveDesc: str = ""  # may do no more this mission

    def __init__(self, bot: BotAI, id: str):
        self.bot = bot
        self.id = id

    async def Do(self):
        print("Do")
