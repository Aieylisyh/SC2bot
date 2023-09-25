import random
from typing import Union
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
from bot.BotSubModule.bot_unitSelection import bot_unitSelection
from bot.BotSubModule.bot_tactics import bot_tactics


class bot_kite:
    bot: BotAI
    unitSelection: bot_unitSelection
    tactics: bot_tactics

    def __init__(self, bot: BotAI):
        self.bot = bot
        self.unitSelection = self.bot.unitSelection
        self.tactics = self.bot.tactics

    def GetNearbyForceEstimate(self, u: Unit, allies: Units):
        res = 0
        nearby0 = self.unitSelection.UnitsInRangeOfUnit(u, allies, 5)
        for a in nearby0:
            res += self.unitSelection.GetUnitPowerValue(a)
        nearby1 = self.unitSelection.UnitsInRangeOfUnit(u, allies, 8)
        for a in nearby1:
            res += self.unitSelection.GetUnitPowerValue(a) * 0.5
        nearby2 = self.unitSelection.UnitsInRangeOfUnit(u, allies, 14)
        for a in nearby2:
            res += self.unitSelection.GetUnitPowerValue(a) * 0.25
        return res
        bot = self.bot
        enemiesUnits = self.unitSelection.GetUnits(True, workers=True)
        eneBuilding = bot.enemy_structures
        enemies: Units = enemiesUnits + eneBuilding
        home_location = self.bot.start_location
        if not enemies:
            return
        allUnits = self.unitSelection.GetUnits(False).ready
        for u in allUnits:
            # print(u)
            await self.UnitAbilityActive(u, enemies)

            info = self.GetGoodAttackInfo(u, 0.05, 5)
            if info[0]:
                await u.attack(info[1])
                continue
            await self.MicroMoveUnit(u, home_location, enemies)
            continue

    # attack only when this attack is very high cost efficiency
    # no wait, high damage bonus, one shot, etc
    def GetGoodAttackInfo(
        self,
        u: Unit,
        cdThreshold: float = 0.5,
        allowShots: int = 4,
        onlyShots: int = -1,
    ) -> tuple[bool, Unit, float]:
        if not u.can_attack:
            return (False, None, 0)
        if u.weapon_cooldown < 0:
            return (False, None, 0)
        bot = self.bot
        if u.weapon_cooldown > cdThreshold:
            return (False, None, 0)

        enemiesUnits = self.unitSelection.GetUnits(True, workers=True)
        if not enemiesUnits:
            return (False, None, 0)
        eneBuilding = bot.enemy_structures
        enemies: Units = enemiesUnits + eneBuilding
        if not enemies:
            return (False, None, 0)

        groundEnes = enemies.filter(lambda u: u.is_structure or (not u.is_flying))
        airEnes = enemies.filter(lambda u: u.is_flying)

        attackableEnes: Units = None
        distCanGo = u.weapon_cooldown * u.movement_speed
        if u.real_speed < u.movement_speed:
            distCanGo * 0.6

        if u.can_attack_ground:
            if attackableEnes:
                attackableEnes.append(
                    self.unitSelection.UnitsInRangeOfUnit(
                        u, groundEnes, u.ground_range + distCanGo
                    )
                )
            else:
                attackableEnes = self.unitSelection.UnitsInRangeOfUnit(
                    u, groundEnes, u.ground_range + distCanGo
                )
        if u.can_attack_air:
            if attackableEnes:
                attackableEnes.append(
                    self.unitSelection.UnitsInRangeOfUnit(
                        u, airEnes, u.air_range + distCanGo
                    )
                )
            else:
                attackableEnes = self.unitSelection.UnitsInRangeOfUnit(
                    u, airEnes, u.air_range + distCanGo
                )
        if not attackableEnes:
            return (False, None, 0)

        for e in attackableEnes:
            dmg = u.calculate_damage_vs_target(e)
            # u.calculate_damage_vs_target
            # Returns a tuple of: [potential damage against target, attack speed, attack range] : Tuple[float, float, float]:
            dmgValue = dmg[0]
            eneHp = e.health + e.shield
            shots = 10
            # print(e)
            if dmgValue > 0:
                shots = float(eneHp) / dmgValue
                if onlyShots > 0 and shots > onlyShots:
                    return (False, None, 0)
            oneShotBonus = 0
            if shots <= 1:
                oneShotBonus = 60
            elif allowShots >= 2 and shots <= 2:
                oneShotBonus = 32
            elif allowShots >= 3 and shots <= 3:
                oneShotBonus = 16
            elif allowShots >= 4 and shots <= 4:
                oneShotBonus = 8
            elif allowShots >= 5 and shots <= 5:
                oneShotBonus = 3
            dmg = u.calculate_damage_vs_target(e)[0]
            e.tpv = (
                dmg
                + oneShotBonus
                + self.unitSelection.DamageDealBonusToAjustAttackPriority(e)
                - u.weapon_cooldown * dmg * 0.6
            )

        eneToAttackSortedList = sorted(
            attackableEnes,
            key=lambda e: e.tpv,
            reverse=True,
        )
        # print(eneToAttackSortedList)
        # print("target " + str(eneToAttackSortedList[0]))
        bestToAttackUnit = eneToAttackSortedList[0]
        return (True, bestToAttackUnit, bestToAttackUnit.tpv)

    # this is to be a very complex algorithm
    # I will implement this step by step
    # this shall be used for all combat units moves
    async def Kite(
        self,
        u: Unit,
        # the self unit to do kite
        futurePosition: Point2,
        # the future position after the fight to go, often enemy base for offensive mode and our base for defensive mode
        thinkRange: float = 10,
        # the range arround the unit to take into consideration,
        # in early game it can be 10 since there is no long range attackers,
        # in mid game vs Terran, tank must be taken into consider so it can be 15, other wise 12 is enough
        # in late game it can be 15
        iteration: int = 4,
        # the algorithm will first check 4 position: up down right left,
        # with a very rough range test to evaluate the threat and contribute score
        # then is the 2nd 3rd 4th iteration...
        #
        #
        #
        #
        damageTolerance: float = 0,
        # with finding a place to go or to attack
        # we will calculate the damage expected to receive
        # we will choose a place with lower damage to take and higher chance to attack enemies,
        # but if the damage exceeed damageTolerance, the unit will not go there
        # the unit will retreat for a while or, retreat completely
        aggressiveFactor: float = 1,
        # how much this unit is tend to involve in a conflict
        # if agressiveFactor is low, this unit will try to attack without take any damage
        # if agressiveFactor is high, this unit will try to attack more, even trade the enemy with its life
        sneakyFactor: float = 0,
        # TODO will not implement this till very late
        # whether should hide from enaging the enemies,
        # #not go approach enemy unless it is the very important target, good to use for DarkTemplar
        group: Units = None,
        # a group of unit that follow's their leader,
        # #but only the leader need costy algorithm,
        # the group is often in 2 3 or 4 units, if small unit like zergling may have 5 or 6 at max
        groupDistance: float = 0.8,
        # swarm the unit's group, the group should not distance for more than this distance
    ):
        bot = self.bot

    def CalculateUnitValue(id: UnitTypeId):
        # base on supply, mineral gas cost, build time, tech height, energy left, passagers inside
        v = 0

        print(v)
