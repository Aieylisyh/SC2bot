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
from bot.BotSubModule.Mission.MissionInstance import MissionState
from bot.BotSubModule.bot_mainStrategy import bot_mainStrategy
from bot.BotSubModule.bot_tactics import bot_tactics
from bot.BotSubModule.bot_unitSelection import bot_unitSelection
from bot.BotSubModule.bot_kite import bot_kite

from bot.BotSubModule.Mission.MissionPrototypes.MissionPrototype import MissionPrototype
from bot.BotSubModule.Mission.MissionPrototypes.AdeptHarass import AdeptHarass
from bot.BotSubModule.Mission.MissionPrototypes.OracleHarass import OracleHarass
from bot.BotSubModule.Mission.MissionPrototypes.VoidrayBasic import VoidrayBasic
from bot.BotSubModule.Mission.MissionPrototypes.BasicArmy import BasicArmy
from bot.BotSubModule.Mission.MissionPrototypes.ObserverScout import ObserverScout


class MissionSystem:
    pendingMissions: set[MissionInstance]
    currentMissions: list[MissionInstance]
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
    kite: bot_kite

    def __init__(self, bot: BotAI):
        self.bot = bot

        self.unitSelection = bot.unitSelection
        self.tactics = bot_tactics(bot)
        self.kite = bot_kite(bot, self.tactics)
        self.mainStrategy = bot_mainStrategy(bot)

        self.pendingMissions = set()
        self.currentMissions = list()
        self.mainStrategy.Init(self)
        for m in self.defaultMissions_test:
            self.AddPending(m)

    async def DoIter1(self):
        # pendingMissions: Set[MissionInstance]
        # currentMissions: [MissionInstance]
        # unitsAssignedMission: Set[int]  # 记录unit的tag的临时表

        # to avoid RuntimeError: Set changed size during iteration
        for m in self.pendingMissions.copy():
            state = await m.CheckState()
            if state == MissionState.Doing:
                self.AddCurrent(m.id)
                self.pendingMissions.remove(m)

        crtMs: list[MissionInstance] = sorted(
            self.currentMissions,
            key=lambda e: e.proto.layer,
            reverse=True,
        )

        for m in crtMs:
            state = await m.CheckState()
            if state == MissionState.Done:
                self.currentMissions.remove(m)
            # m.Do()
        return
        await self.tactics.ScoutWithOb()
        # await self.tactics.OracleRush()
        await self.tactics.CancelAttackedBuildings()
        await self.mainStrategy.BattleMacro()
        await self.tactics.Micro()

    async def DoIter3(self):
        return
        await self.mainStrategy.Rush()

    async def DoIter10(self):
        return
        await self.mainStrategy.Rally()

    def AddCurrent(self, id: str):
        proto = self.GetPrototype(id)
        m = MissionInstance(self.bot, proto, self.kite)
        m.state = MissionState.Doing
        m.iter = 0
        self.currentMissions += [m]
        print("add crt mission " + proto.id)

    def AddPending(self, id: str):
        if self.GetPending(id):
            return
        proto = self.GetPrototype(id)
        m = MissionInstance(self.bot, proto, self.kite)
        m.state = MissionState.Pending
        m.iter = 0
        self.pendingMissions.add(m)
        print("add pending mission " + proto.id)

    def GetCurrents(self, id: str) -> [MissionInstance]:
        return [i for i, x in enumerate(self.currentMissions) if x.id == id]

    def GetPending(self, id: str) -> MissionInstance:
        for m in self.pendingMissions:
            if m.id == id:
                return m
        return None

    def GetPrototype(self, id: str) -> MissionPrototype:
        if id == "AdeptHarass":
            return AdeptHarass(self.bot, id)
        elif id == "OracleHarass":
            return OracleHarass(self.bot, id)
        elif id == "ObserverScout":
            return ObserverScout(self.bot, id)
        elif id == "VoidrayBasic":
            return VoidrayBasic(self.bot, id)
        return BasicArmy(self.bot, "BasicArmy")

    def GetPrototypeClass(id: str) -> MissionPrototype:
        if id == "AdeptHarass":
            return AdeptHarass
        elif id == "OracleHarass":
            return OracleHarass
        elif id == "ObserverScout":
            return ObserverScout
        elif id == "VoidrayBasic":
            return VoidrayBasic
        return BasicArmy

    def HasUnits(self, unitID: UnitTypeId, amount: int):
        bot = self.bot
        bot.units(UnitTypeId.ORACLE).ready.amount
        self.unitSelection.GetUnits()
        return False
