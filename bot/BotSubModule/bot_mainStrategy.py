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
    attackForce_min_supply: int = -2
    buildStructure: bot_buildStructure

    def __init__(self, bot: BotAI):
        self.bot = bot
        self.unitSelection = bot.unitSelection
        self.tactics = bot.tactics
        self.buildStructure = bot.buildStructure

    def GetLaunchAttackUnitSupplyCap(self):
        bot = self.bot

        return (
            self.attackForce_min_supply
            + bot.townhalls.ready.amount * 15
            - bot.townhalls.not_ready.amount * 20
            + bot.supply_left
        )

    async def Rush(self):
        bot = self.bot
        if bot.startingGame_stalkersRushed:
            return
        myForces = self.unitSelection.GetUnits(False)
        if myForces.amount >= 2:
            target = bot.enemy_start_locations[0].position
            for f in myForces:
                if f.can_attack:
                    f.attack(target)
            print("startingGame_stalkersRushed")
            bot.startingGame_stalkersRushed = True

    def AttackWithAllForces(self, includeWorkers: bool = True):
        bot = self.bot
        forces = self.unitSelection.GetUnits(False, workers=includeWorkers)
        forces = self.unitSelection.FilterAttack(forces)
        t = bot.enemy_start_locations[0]
        for unit in forces:
            if unit.can_attack:
                unit.attack(t)
            else:
                unit.move(t)

    async def BattleMacro(self):
        bot = self.bot
        if bot.supply_army > self.GetLaunchAttackUnitSupplyCap():
            self.AttackWithAllForces(False)
            return

        await self.Defend()

    async def Defend(self):
        # attack invaders
        bot = self.bot
        enes = self.unitSelection.GetUnits(True, workers=True)
        if enes:
            ts = bot.townhalls.ready
            invaders: Units = None
            for t in ts:
                if not invaders:
                    invaders == enes.closer_than(24, t)
                else:
                    invaders.append(enes.closer_than(24, t))
            if invaders:
                p = invaders.center
                forces = self.unitSelection.GetUnits(False).ready.idle
                forces.append(self.unitSelection.GetUnits(False).closer_than(20, p))
                if forces:
                    for unit in forces:
                        if unit.can_attack:
                            unit.attack(p)

    async def Rally(self):
        bot = self.bot
        if bot.structures.ready.amount < 3:
            return

        amy = self.unitSelection.GetUnits(False).idle
        if not amy:
            return
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
        for unit in amy:
            # print("rally " + str(unit))
            if unit.can_attack:
                unit.attack(rallyPos)
            else:
                unit.move(rallyPos)
            # unit.patrol(t1, True)
