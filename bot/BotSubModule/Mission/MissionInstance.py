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
from bot.BotSubModule.Mission.MissionPrototypes.MissionPrototype import MissionPrototype
import asyncio


class MissionInstance:
    finished: bool
    started: bool
    id: str
    id: str
    proto: MissionPrototype

    targetUnit: Unit
    targetPosition: Point2
    targetUnits: Units
    targetDuration: float
    targetAmount: int

    layer: int
    piority: int
    startIteraction: int

    def __init__(self, bot: BotAI, mp: MissionPrototype):
        self.bot = bot
        self.proto = mp
        self.Initialize()

    def CheckToStart(self) -> bool:
        return False

    def CheckFinish(self) -> bool:
        return False

    async def Do(self):
        await self.proto.Do()

    def Initialize(self):
        self.id = self.proto.id
        print("mission instance " + str(self.proto))
