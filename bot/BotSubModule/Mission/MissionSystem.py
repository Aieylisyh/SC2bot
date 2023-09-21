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

from bot.BotSubModule.Mission.MissionInstance import MissionInstance
from bot.BotSubModule.bot_mainStrategy import bot_mainStrategy
from bot.BotSubModule.bot_tactics import bot_tactics
from bot.BotSubModule.bot_unitSelection import bot_unitSelection

from bot.BotSubModule.Mission.MissionPrototypes.MissionPrototype import MissionPrototype
from Mission.MissionPrototypes.AdeptHarass import AdeptHarass
from Mission.MissionPrototypes.OracleHarass import OracleHarass
from bot.BotSubModule.Mission.MissionPrototypes.VoidrayBasic import VoidrayBasic
from bot.BotSubModule.Mission.MissionPrototypes.BasicArmy import BasicArmy
from bot.BotSubModule.Mission.MissionPrototypes.ObserverScout import ObserverScout


class MissionSystem:
    pendingMissions: Set[MissionInstance]
    currentMissions: [MissionInstance]
    unitsAssignedMission: Set[int]  # 记录unit的tag的临时表

    defaultMissions_test: Set[str] = [
        "AdeptHarass",
        "OracleHarass",
        "ObserverScout",
        "VoidrayBasic",
        "",
    ]

    defaultMissions_base: Set[str]
    defaultMissions_PvP: Set[str]
    defaultMissions_PvT: Set[str]
    defaultMissions_PvZ: Set[str]
    defaultMissions_TvP: Set[str]
    defaultMissions_TvT: Set[str]
    defaultMissions_TvZ: Set[str]
    defaultMissions_ZvP: Set[str]
    defaultMissions_ZvT: Set[str]
    defaultMissions_ZvZ: Set[str]

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

        for m in self.defaultMissions_test:
            self.AddPending(m)

    async def DoIter1(self):
        # pendingMissions: Set[MissionInstance]
        # currentMissions: [MissionInstance]
        # unitsAssignedMission: Set[int]  # 记录unit的tag的临时表

        for m in self.crtMissions:
            m.Do()
            # check start not start missions, delete useless missions
            # add running missions to
        return
        await self.tactics.ScoutWithOb()
        # await self.tactics.OracleRush()
        await self.tactics.CancelAttackedBuildings()
        await self.mainStrategy.BattleMacro()
        await self.tactics.Micro()

    async def DoIter3(self):
        await self.mainStrategy.Rush()

    async def DoIter10(self):
        await self.mainStrategy.Rally()

    def AddCurrent(self, id: str):
        proto = MissionSystem.GetPrototype(id)
        self.currentMissions += MissionInstance(self.bot, proto)
        print("add crt mission " + id)

    def AddPending(self, id: str):
        if self.GetPending(id):
            return
        proto = MissionSystem.GetPrototype(id)
        self.pendingMissions.add(MissionInstance(self.bot, proto))

    def GetCurrents(self, id: str) -> [MissionInstance]:
        return [i for i, x in enumerate(self.currentMissions) if x.id == id]

    def GetPending(self, id: str) -> MissionInstance:
        for m in self.pendingMissions:
            if m.id == id:
                return m
        return None

    def GetPrototype(id: str) -> MissionPrototype:
        if id == "AdeptHarass":
            return AdeptHarass
        elif id == "OracleHarass":
            return OracleHarass
        elif id == "ObserverScout":
            return ObserverScout
        elif id == "VoidrayBasic":
            return VoidrayBasic
        return BasicArmy
