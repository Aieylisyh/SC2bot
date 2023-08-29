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
import asyncio


class bot_tactics:
    bot: BotAI
    scoutTargetIndex: int
    ordered_expansions: None
    unitSelection: bot_unitSelection

    def __init__(self, bot: BotAI):
        self.bot = bot
        self.scouts_and_spots = {}
        self.scoutTargetIndex = 0
        self.ordered_expansions = None
        self.unitSelection = bot.unitSelection
        self

    # Cancel building on attack
    async def CancelAttackedBuildings(self):
        bot = self.bot
        for s in bot.structures.not_ready:
            if (
                s.build_progress < 1
                and s.build_progress > 0.15
                and s.shield_health_percentage < 0.25
            ):
                enes = self.unitSelection.GetInRangeUnits(
                    s, 8, self.unitSelection.GetUnits(True)
                )
                if enes.amount > 1:
                    s(AbilityId.CANCEL, s)

    async def ScoutWithOb(self):
        # Method to send our obs scouting
        # We retrieve the list of possible extensions
        bot = self.bot
        # self.ordered_expansions = None
        if not self.ordered_expansions or len(self.ordered_expansions) == 0:
            self.ordered_expansions = sorted(
                # You are using 'self.expansion_locations', please use 'self.expansion_locations_list' (fast) or 'self.expansion_locations_dict' (slow) instead.
                bot.expansion_locations_list,
                key=lambda el: el.distance_to(bot.enemy_start_locations[0]),
                reverse=False,
            )
        # MORPH_OBSERVERMODE = 3739
        # MORPH_SURVEILLANCEMODE = 3741
        for obs in bot.units(UnitTypeId.OBSERVERSIEGEMODE).ready:
            detectors = self.unitSelection.GetInRangeEnemyDetectors(obs, obs)
            if detectors and detectors.amount > 0:
                obs(AbilityId.MORPH_OBSERVERMODE, queue=False)
                # direction = obs.position.offset(bot.start_location)
                direction = obs.position.negative_offset(
                    detectors.closest_n_units(obs, 1).first.position
                )
                obs.move(obs.position + direction.normalized * 8, queue=True)
                continue

            otherObs = self.unitSelection.GetInRangeAllyObservers(
                obs, obs.sight_range - 2
            )
            if otherObs and otherObs.amount > 0:
                obs(AbilityId.MORPH_OBSERVERMODE, queue=False)
                direction = obs.position.negative_offset(
                    otherObs.closest_n_units(obs, 1).first.position
                )
                obs.move(obs.position + direction.normalized * 6, queue=True)
                continue

            enes = self.unitSelection.GetInRangeUnits(
                obs, obs, self.unitSelection.GetUnits(True)
            )
            if not enes or enes.amount < 3:
                obs(AbilityId.MORPH_OBSERVERMODE, queue=False)

        for ob in bot.units(UnitTypeId.OBSERVER).ready:
            detectors = self.unitSelection.GetInRangeEnemyDetectors(ob, ob)
            if detectors and detectors.amount > 0:
                # direction = obs.position.offset(bot.start_location)
                direction = ob.position.negative_offset(
                    detectors.closest_n_units(ob, 1).first.position
                )
                ob.move(ob.position + direction.normalized * 8)
                continue
            enes = self.unitSelection.GetInRangeUnits(
                ob, ob, self.unitSelection.GetUnits(True)
            )
            otherObs = self.unitSelection.GetInRangeAllyObservers(
                ob, ob.sight_range, UnitTypeId.OBSERVERSIEGEMODE
            )
            otherOb = self.unitSelection.GetInRangeAllyObservers(
                ob, ob.sight_range, UnitTypeId.OBSERVER
            )
            if enes and enes.amount > 4 and not otherObs and not otherOb:
                ob(AbilityId.MORPH_SURVEILLANCEMODE, queue=False)
                continue

            if ob.is_idle:
                # scout
                maxIndex = 3
                if len(self.ordered_expansions) < 4:
                    maxIndex = 0
                elif len(self.ordered_expansions) < 6:
                    maxIndex = 1
                elif len(self.ordered_expansions) < 8:
                    maxIndex = 2
                targetLocation = self.ordered_expansions[self.scoutTargetIndex]
                self.scoutTargetIndex += 1
                if self.scoutTargetIndex > maxIndex:
                    self.scoutTargetIndex = 0
                ob.move(targetLocation)

    # Our method to micro and to blink
    async def StalkerEscape(
        self, stalker: Unit, home_location: Point2, enemies_can_attack: Units
    ):
        bot = self.bot
        escape_location = stalker.position.towards(home_location, 5)
        # Threats that can attack the stalker
        enemyThreatsClose1: Units = enemies_can_attack.filter(
            lambda unit: unit.distance_to(stalker) > 8
            and unit.distance_to(stalker) <= 12
        )
        enemyThreatsClose2: Units = enemies_can_attack.filter(
            lambda unit: unit.distance_to(stalker) > 6
            and unit.distance_to(stalker) <= 8
        )
        enemyThreatsClose3: Units = enemies_can_attack.filter(
            lambda unit: unit.distance_to(stalker) <= 6
        )
        enemyThreatsClose: Units = enemies_can_attack.filter(
            lambda unit: unit.distance_to(stalker) <= 12
        )
        threatRating = 0
        for e in enemyThreatsClose1:
            threatRating += bot.calculate_supply_cost(e.type_id) * 1
        for e in enemyThreatsClose2:
            threatRating += bot.calculate_supply_cost(e.type_id) * 2
        for e in enemyThreatsClose3:
            threatRating += bot.calculate_supply_cost(e.type_id) * 3
        shouldRetreat = (threatRating > 12 and stalker.shield_percentage < 0.5) or (
            threatRating > 8 and stalker.shield_percentage < 0.1
        )
        if shouldRetreat:
            abilities = await self.bot.get_available_abilities(stalker)
            if AbilityId.EFFECT_BLINK_STALKER in abilities:
                # await self.bot.order(stalker, EFFECT_BLINK_STALKER, escape_location)
                stalker(AbilityId.EFFECT_BLINK_STALKER, escape_location)
                return
            else:
                distanceRetreat = 2
                retreatPoints: Set[Point2] = self.unitSelection.around8(
                    stalker.position, distance=distanceRetreat
                ) | self.unitSelection.around8(
                    stalker.position, distance=distanceRetreat * 2
                )
                # Filter points that are pathable
                retreatPoints: Set[Point2] = {
                    x for x in retreatPoints if self.bot.in_pathing_grid(x)
                }
                if retreatPoints:
                    closestEnemy: Unit = enemyThreatsClose.closest_to(stalker)
                    retreatPoint: Unit = closestEnemy.position.furthest(retreatPoints)
                    stalker.move(retreatPoint)
                    return

    async def MoveUnitsTogether(self, u: Unit, home_location: Point2):
        allies = self.unitSelection.GetUnits(False)
        nearby = self.unitSelection.UnitsInRangeOfUnit(u, allies, 4.5)
        if not nearby:
            return

        if nearby.amount > 2:
            p = nearby.center
            u.move(p)
            return

        n: Unit = nearby.closest_to(u)
        if (
            n.distance_to_squared(home_location)
            < u.distance_to_squared(home_location) + 1
        ):
            u.move(n.position)

    async def MicroMoveUnit(
        self, u: Unit, home_location: Point2, enemies_can_attack: Units
    ):
        # TODO chase weak target enemies or hide from enemies
        # only move, no attack
        bot = self.bot
        enemies = self.unitSelection.GetUnits(True, workers=True)
        if not enemies:
            return
        nearestEne: Unit = enemies.closest_to(u)
        isMeleeFactor = 1
        if u._weapons and u._weapons[0].range <= 2:
            isMeleeFactor = 10
        elif u._weapons and u._weapons[0].range <= 4:
            isMeleeFactor = 2.5

        if isMeleeFactor >= 10:
            u.move(u.position.towards(nearestEne.position))
            return

        # print("nearestEne " + str(nearestEne))
        dir = u.position.offset(nearestEne.position).normalized

        allies = self.unitSelection.GetUnits(False)
        allies = self.unitSelection.FilterAttack(allies)
        allies = allies.ready.filter(lambda unit: not unit == u)
        allyForce = self.GetNearbyForceEstimate(u, allies) * isMeleeFactor
        eneForce = self.GetNearbyForceEstimate(u, enemies)
        weAreStronger = allyForce > eneForce * 1.5
        weAreWeaker = allyForce < eneForce * 1
        if weAreStronger:
            u.move(u.position.towards(nearestEne.position))
            return

        if u.type_id == UnitTypeId.STALKER and (random.random() > 0.5 or weAreWeaker):
            await self.StalkerEscape(u, home_location, enemies_can_attack)

        if weAreWeaker:
            if random.random() > 0.4:
                u.move(u.position - dir)
            else:
                await self.MoveUnitsTogether(u, home_location)
        else:
            await self.MoveUnitsTogether(u, home_location)

    def GetNearbyForceEstimate(self, u: Unit, allies: Units):
        res = 0
        nearby0 = self.unitSelection.UnitsInRangeOfUnit(u, allies, 4.5)
        for a in nearby0:
            res += self.unitSelection.GetUnitPowerValue(a)
        nearby1 = self.unitSelection.UnitsInRangeOfUnit(u, allies, 7)
        for a in nearby1:
            res += self.unitSelection.GetUnitPowerValue(a) * 0.5
        nearby2 = self.unitSelection.UnitsInRangeOfUnit(u, allies, 10)
        for a in nearby2:
            res += self.unitSelection.GetUnitPowerValue(a) * 0.25
        return res

    async def TryAttackNearbyEnemy(self, u: Unit, rangeAdd: float):
        bot = self.bot
        unitSelection = self.unitSelection
        enemies = self.unitSelection.GetUnits(True, workers=True)
        attackableEnes = enemies.in_attack_range_of(u, rangeAdd)
        if not attackableEnes:
            return
        if attackableEnes.amount == 1:
            u.attack(attackableEnes.first)  # closest_n_units
            return
        for e in attackableEnes:
            dmg = u.calculate_damage_vs_target(e)
            dieUnits = []
            dmgValue = dmg[0]
            eneHp = e.health + e.shield
            shots = eneHp / dmgValue
            if shots <= 1:
                dieUnits.append(e)
            if len(dieUnits) > 0:
                dieUnits = sorted(
                    dieUnits,
                    key=lambda du: dmgValue
                    + unitSelection.DamageDealBonusToAjustAttackPriority(du),
                    reverse=False,
                )
                u.attack(dieUnits[0])
                return
            bonusPriority = 0
            if shots <= 2:
                bonusPriority = 31
            elif shots <= 3:
                bonusPriority = 20
            elif shots <= 4:
                bonusPriority = 13
            elif shots <= 5:
                bonusPriority = 8
            eneToAttackSortedList = sorted(
                attackableEnes,
                key=lambda e: u.calculate_damage_vs_target(e)[0]
                + self.unitSelection.DamageDealBonusToAjustAttackPriority(e)
                + bonusPriority,
                reverse=False,
            )
            u.attack(eneToAttackSortedList[0])

    async def SentryForceField(self, u: Unit, enes: Units):
        if u.type_id == UnitTypeId.SENTRY:
            abilities = await self.bot.get_available_abilities(u)
            if AbilityId.GUARDIANSHIELD_GUARDIANSHIELD in abilities:
                allies = self.unitSelection.GetUnits(False, True, False)
                allies = self.unitSelection.UnitsInRangeOfUnit(u, allies, 5)
                if allies.amount <= 3:
                    return

                enes = self.unitSelection.UnitsInRangeOfUnit(u, enes, 10)
                enes = self.unitSelection.FilterAttack()
                rangedEneAmount = 0
                for e in enes:
                    if (
                        e.can_attack_ground
                        and e._weapons[0]
                        and e._weapons[0].range > 3
                    ):
                        rangedEneAmount += 1
                if rangedEneAmount > 3:
                    u(AbilityId.GUARDIANSHIELD_GUARDIANSHIELD)

    async def Micro(self):
        bot = self.bot
        enemies = self.unitSelection.GetUnits(True, workers=True)
        # enemies_air = self.GetAirEnemies()
        # enemies_ground = self.GetGroundEnemies()

        home_location = self.bot.start_location
        # enemies_can_attack: Units = enemies.filter(lambda unit: unit.can_attack_ground)
        if not enemies:
            return

        for u in bot.units.ready:
            if not u.can_attack:
                continue
            if u.weapon_cooldown < 0:
                continue

            if u.weapon_cooldown > 0.02:
                await self.MicroMoveUnit(u, home_location, enemies)
                continue

            await self.SentryForceField(u, enemies)
            enes = enemies.in_attack_range_of(u)
            attackableEnes = enes
            # TODO refactor with
            # closer_than
            # in_attack_range_of
            # stalker.radius
            # stalker.move(enemy_fighters.closest_to(stalker))
            # closest_enemy.position.towards(stalker, distance)
            if not attackableEnes:
                await self.TryAttackNearbyEnemy(u, 2)
                continue
            if attackableEnes.amount == 1:
                u.attack(attackableEnes.first)  # closest_n_units
                continue
            for e in attackableEnes:
                dmg = u.calculate_damage_vs_target(e)
                if dmg[0] > e.health + e.shield:
                    u.attack(e)
                    continue
            eneToAttackSortedList = sorted(
                attackableEnes,
                key=lambda e: u.calculate_damage_vs_target(e)[0],
                reverse=False,
            )
            u.attack(eneToAttackSortedList[0])
            continue
            # u.calculate_damage_vs_target
            # Returns a tuple of: [potential damage against target, attack speed, attack range] : Tuple[float, float, float]:
