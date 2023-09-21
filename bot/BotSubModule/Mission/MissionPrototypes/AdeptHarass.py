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


class AdeptHarass(MissionPrototype):
    def __init__(self, bot: BotAI):
        self.bot = bot
        print("__init__: AdeptHarass")

    async def Do(self):
        print("Do: AdeptHarass")
