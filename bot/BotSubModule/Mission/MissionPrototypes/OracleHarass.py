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
from bot.BotSubModule.Mission.MissionInstance import MissionInstance
import asyncio


class OracleHarass(MissionPrototype):
    uid: UnitTypeId = UnitTypeId.ORACLE
    times: int = 2
    AmountMin = 1
    AmountMax = 3
    energyMinStartMission = 30
    energyMinStartAttack = 34

    def __init__(self, bot: BotAI, id: str):
        super().__init__(bot, id)

    async def Do(self):
        print("Do: OracleHarass")
