import string
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

from bot.BotSubModule.bot_buildStructure import bot_buildStructure
from bot.BotSubModule.bot_economy import bot_economy
from bot.BotSubModule.bot_trainArmy import bot_trainArmy
from bot.BotSubModule.bot_nexusSkill import bot_nexusSkill
from bot.BotSubModule.bot_tech import bot_tech
from bot.BotSubModule.Mission.MissionSystem import MissionSystem
from bot.BotSubModule.bot_unitSelection import bot_unitSelection

# learn source：https://brax.gg/python-sc2-advanced-bot/


class StalkerRushBot(BotAI):
    NAME: str = "StalkerRush"
    RACE: Race = Race.Protoss

    iter3: int = 0
    iter10: int = 0

    mission: MissionSystem
    buildStructure: bot_buildStructure
    economy: bot_economy
    tech: bot_tech
    trainArmy: bot_trainArmy
    nexusSkill: bot_nexusSkill
    unitSelection: bot_unitSelection

    startingGame_rusherBuilt: int = 0
    midEarlyGame_oracleBuilt: int = 0
    midEarlyGame_oracleRushed: bool = False

    async def DoIter10(self):
        self.iter10 += 1
        await self.mission.DoIter10()

    async def DoIter3(self):
        self.iter3 += 1
        await self.economy.BuildAssimilators()
        await self.economy.DistributeWorkers()
        await self.mission.DoIter3()

    async def on_start(self):
        self.buildStructure = bot_buildStructure(self)
        self.economy = bot_economy(self)
        self.tech = bot_tech(self)
        self.trainArmy = bot_trainArmy(self)
        self.nexusSkill = bot_nexusSkill(self)
        self.unitSelection = bot_unitSelection(self)
        self.mission = MissionSystem(self)
        await self.economy.StartGameAllocateWorkers()

    async def on_end(self, result):
        print("Game ended.")
        print(str(result))

    async def on_step(self, iteration):
        if not self.townhalls.ready:
            t = self.enemy_start_locations[0]
            for unit in self.units.ready:
                if unit.can_attack:
                    unit.attack(t)
                else:
                    unit.move(t)
            return

        if iteration == 0:
            await self.chat_send("(glhf)")
        # print("tick "+ str(iteration))
        await self.economy.TrainWorkers()
        await self.tech.forge_research()
        await self.buildStructure.build_productions()
        await self.buildStructure.BuildPylons()
        await self.trainArmy.train()
        await self.economy.Expand()
        await self.nexusSkill.ChronoBoost()
        await self.mission.DoIter1()

        if iteration % 10 == 9:
            await self.DoIter10()
        if iteration % 3 == 2:
            await self.DoIter3()
