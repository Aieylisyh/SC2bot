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
from bot.BotSubModule.bot_mainStrategy import bot_mainStrategy
from bot.BotSubModule.bot_tactics import bot_tactics
from bot.BotSubModule.bot_unitSelection import bot_unitSelection
from bot.BotSubModule.bot_trainArmy import bot_trainArmy
from bot.BotSubModule.bot_nexusSkill import bot_nexusSkill
from bot.BotSubModule.bot_tech import bot_tech

# learn source：https://brax.gg/python-sc2-advanced-bot/


class StalkerRushBot(BotAI):
    NAME: str = "StalkerRush"
    RACE: Race = Race.Protoss

    iter3: int = 0
    iter10: int = 0

    buildStructure: bot_buildStructure
    economy: bot_economy
    mainStrategy: bot_mainStrategy
    tactics: bot_tactics
    tech: bot_tech
    unitSelection: bot_unitSelection
    trainArmy: bot_trainArmy
    nexusSkill: bot_nexusSkill

    def AttackWithAllForces(self):
        all_attack_units = bot_unitSelection.all_units(self)
        t = self.enemy_start_locations[0]
        for unit in all_attack_units:
            if unit.can_attack:
                unit.attack(t)

    async def DoIter10(self):
        self.iter10 += 1

    async def DoIter3(self):
        self.iter3 += 1
        await self.economy.BuildAssimilators()
        await self.economy.DistributeWorkers()
        # print("DoIter3")

    def LaunchAttack(self):
        if self.already_pending_upgrade(UpgradeId.BLINKTECH) < 0.9:
            return

        myForces = self.GetAllCombatForces()
        if myForces.amount > self.attackForce_count:
            # targets = (self.enemy_units | self.enemy_structures).filter(lambda unit: unit.can_be_attacked)
            target = self.enemy_start_locations[0].position
            for f in myForces.idle:
                if f.can_attack:
                    f.attack(target)
                else:
                    f.move(target)
        return

    async def on_start(self):
        print("StalkerRushBot Game started")
        self.buildStructure = bot_buildStructure(self)
        self.economy = bot_economy(self)
        self.mainStrategy = bot_mainStrategy(self)
        self.tactics = bot_tactics(self)
        self.tech = bot_tech(self)
        self.unitSelection = bot_unitSelection(self)
        self.trainArmy = bot_trainArmy(self)
        self.nexusSkill = bot_nexusSkill(self)

        await self.economy.StartGameAllocateWorkers()

    async def on_end(self, result):
        print("Game ended.")
        print(str(result))

    async def on_step(self, iteration):
        if not self.townhalls.ready:
            self.AttackWithAllForces()
            return

        if iteration % 10 == 0:
            await self.DoIter10()
        if iteration % 3 == 0:
            await self.DoIter3()

        if iteration == 0:
            await self.chat_send("(glhf)")
        # print("tick "+ str(iteration))
        await self.economy.TrainWorkers()
        await self.tactics.micro()
        await self.tech.forge_research()
        await self.buildStructure.build_productions()
        await self.buildStructure.BuildPylons()
        await self.trainArmy.train()
        await self.economy.Expand()
        await self.nexusSkill.ChronoBoost()
        return
