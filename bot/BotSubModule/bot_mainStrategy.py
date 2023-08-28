import random
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
from bot.BotSubModule.bot_unitSelection import bot_unitSelection
from bot.BotSubModule.bot_tactics import bot_tactics
from bot.BotSubModule.bot_buildStructure import bot_buildStructure


class bot_mainStrategy:
    bot: BotAI
    unitSelection: bot_unitSelection
    tactics: bot_tactics
    attackForce_supply: int = 42
    buildStructure: bot_buildStructure

    def __init__(self, bot: BotAI):
        self.bot = bot
        self.unitSelection = bot.unitSelection
        self.tactics = bot.tactics
        self.buildStructure = bot.buildStructure

    async def Rush(self):
        bot = self.bot
        if bot.startingGame_stalkersRushed:
            return
        myForces = self.tactics.GetAllCombatForces()
        if myForces.amount >= 2:
            target = bot.enemy_start_locations[0].position
            bot.startingGame_stalkersRushed = True
            for f in myForces.idle:
                if f.can_attack:
                    f.attack(target)

    def AttackWithAllForces(self, includeWorkers: bool = True):
        bot = self.bot
        all_attack_units = self.unitSelection.all_units()
        if not includeWorkers:
            all_attack_units = self.unitSelection.all_amy()

        t = bot.enemy_start_locations[0]
        for unit in all_attack_units:
            if unit.can_attack:
                unit.attack(t)

    def LaunchAttack(self):
        bot = self.bot
        if bot.already_pending_upgrade(UpgradeId.BLINKTECH) < 0.9:
            return

        myForces = self.tactics.GetAllCombatForces()
        if myForces.amount > self.attackForce_count:
            # targets = (self.enemy_units | self.enemy_structures).filter(lambda unit: unit.can_be_attacked)
            target = bot.enemy_start_locations[0].position
            for f in myForces.idle:
                if f.can_attack:
                    f.attack(target)
        return

    async def BattleMacro(self):
        bot = self.bot
        if bot.supply_army > self.attackForce_supply:
            self.AttackWithAllForces(False)
        else:
            enes = self.tactics.GetEnemyAmy()
            if enes:
                ts = bot.townhalls.ready
                invaders: Units = None
                for t in ts:
                    invaders == enes.closer_than(15, t)
                if invaders:
                    all_attack_units = self.unitSelection.all_amy().idle
                    for unit in all_attack_units:
                        if unit.can_attack:
                            unit.attack(invaders.closest_to(unit).position)
                else:
                    self.Rally()
            else:
                self.Rally()

    def Rally(self):
        bot = self.bot
        if bot.structures.ready.amount < 3:
            return

        all_attack_units = self.unitSelection.all_amy().idle
        # t = bot.townhalls.first.position
        # if self.buildStructure.base2MainPylon:
        #    t = self.buildStructure.base2MainPylon.position
        # else:
        #    dir = bot.start_location.offset(bot.enemy_start_locations[0])
        #    t = bot.main_base_ramp.top_center + dir.normalized * 3
        building2 = bot.structures.ready.closest_n_units(
            bot.enemy_start_locations[0], 2
        )

        # dir = bot.start_location.negative_offset(bot.enemy_start_locations[0])
        # rallyPos = t + dir.normalized * 4
        rallyPos = 0.5 * (building2[0].position + building2[1].position)
        # t1 = t - dir.normalized * 2
        for unit in all_attack_units.idle:
            if unit.can_attack:
                unit.attack(rallyPos)
            else:
                unit.move(rallyPos)
            # unit.patrol(t1, True)
