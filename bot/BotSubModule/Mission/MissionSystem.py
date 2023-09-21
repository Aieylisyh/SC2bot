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
from bot.BotSubModule.Mission.MissionPrototypes.MissionPrototype import MissionPrototype
from Mission.MissionInstance import MissionInstance


class MissionSystem:
    crtMissions: Set[MissionInstance]

    defaultMissions_basic: Set[MissionInstance]
    defaultMissions_PvP: Set[MissionInstance]
    defaultMissions_PvT: Set[MissionInstance]
    defaultMissions_PvZ: Set[MissionInstance]
    defaultMissions_TvP: Set[MissionInstance]
    defaultMissions_TvT: Set[MissionInstance]
    defaultMissions_TvZ: Set[MissionInstance]
    defaultMissions_ZvP: Set[MissionInstance]
    defaultMissions_ZvT: Set[MissionInstance]
    defaultMissions_ZvZ: Set[MissionInstance]

    def __init__(self, bot: BotAI):
        self.bot = bot

    async def Execute(self):
        return False
