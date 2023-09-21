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
    units: Units

    targetUnit: Unit
    targetPosition: Point2
    targetUnits: Units
    targetDuration: float
    targetAmount: int

    layer: int
    piority: int
    startIteraction: int

    def __init__(self, bot: BotAI):
        self.bot = bot

    def TargetChecker(self) -> bool:
        return False

    def DoMissionTasks(self) -> bool:
        return False

    def Initialize(self, id: str):
        self.started = False
        self.finished = False
        id = str
        if self.id == "":
            # dosomething
            print(self.id)
        elif self.id == "1":
            # dosomething
            print(self.id)
        elif self.id == "2":
            # dosomething
            print(self.id)
        elif self.id == "3":
            # dosomething
            print(self.id)

    def CheckFinish(self):
        if not self.started:
            return False

        if self.id == "":
            # dosomething
            print(self.id)
        elif self.id == "1":
            # dosomething
            print(self.id)
        elif self.id == "2":
            # dosomething
            print(self.id)
        elif self.id == "3":
            # dosomething
            print(self.id)
        else:
            return False
