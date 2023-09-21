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
from bot.BotSubModule.Mission.MissionInstance import MissionInstance
from bot.BotSubModule.bot_mainStrategy import bot_mainStrategy
from bot.BotSubModule.bot_tactics import bot_tactics
from bot.BotSubModule.bot_unitSelection import bot_unitSelection


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

    mainStrategy: bot_mainStrategy
    tactics: bot_tactics
    unitSelection: bot_unitSelection

    def __init__(self, bot: BotAI):
        self.bot = bot
        self.unitSelection = bot_unitSelection(bot)
        self.tactics = bot_tactics(bot)
        self.mainStrategy = bot_mainStrategy(bot)

    async def Init(self):
        self.tactics.Init()
        self.mainStrategy.Init()

    async def DoIter1(self):
        await self.tactics.ScoutWithOb()
        # await self.tactics.OracleRush()
        await self.tactics.CancelAttackedBuildings()
        await self.mainStrategy.BattleMacro()
        await self.tactics.Micro()
        return False

    async def DoIter3(self):
        await self.mainStrategy.Rush()

    async def DoIter10(self):
        await self.mainStrategy.Rally()
