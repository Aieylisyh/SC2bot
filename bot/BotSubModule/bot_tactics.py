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
import asyncio


class bot_tactics:
    bot: BotAI
    scoutTargetIndex: int
    ordered_expansions: None

    def __init__(self, bot: BotAI):
        self.bot = bot
        self.scouts_and_spots = {}
        self.scoutTargetIndex = 0
        self.ordered_expansions = None

    def GetEnemies(self) -> Units:
        bot = self.bot
        return bot.enemy_units.filter(
            lambda unit: unit.type_id not in {UnitTypeId.LARVA, UnitTypeId.EGG}
        )

    def GetAirEnemies(self) -> Units:
        bot = self.bot
        return bot.enemy_units.filter(
            lambda unit: (unit.type_id not in {UnitTypeId.LARVA, UnitTypeId.EGG})
            and unit.is_flying
        )

    def GetGroundEnemies(self) -> Units:
        bot = self.bot
        return bot.enemy_units.filter(
            lambda unit: (unit.type_id not in {UnitTypeId.LARVA, UnitTypeId.EGG})
            and not unit.is_flying
        )

    def GetEnemyDetectors(self) -> Units:
        bot = self.bot
        return bot.enemy_units.filter(lambda unit: unit.is_detector)

    def GetEnemyAmy(self) -> Units:
        bot = self.bot
        enes = self.GetEnemies()
        if enes.empty:
            return None
        return enes.filter(lambda u: u.can_attack) + bot.enemy_structures(
            {
                UnitTypeId.BUNKER,
                UnitTypeId.MISSILETURRET,
                UnitTypeId.SPINECRAWLER,
                UnitTypeId.SPORECANNON,
                UnitTypeId.PHOTONCANNON,
            }
        )

    def UnitsInRangeOfUnit(self, u: Unit, us: Units, range: float) -> Units:
        return us.filter(
            lambda v: self.bot._distance_squared_unit_to_unit(u, v) < range * range
        )

    def GetInRangeEnemies(self, u: Unit, range: Union[Unit, float], enes: Units):
        if not enes:
            enes = self.GetEnemies()
        if enes.empty:
            return None
        if isinstance(range, Unit):
            return self.UnitsInRangeOfUnit(u, enes, range.sight_range)
        return self.UnitsInRangeOfUnit(u, enes, range)

    def GetInRangeAllyObs(
        self,
        u: Unit,
        range: Union[Unit, float],
        id: UnitTypeId = UnitTypeId.OBSERVERSIEGEMODE,
    ) -> Units:
        others = self.bot.units(id).ready
        if u in others:
            others.remove(u)
        if others.empty:
            return None
        if isinstance(range, Unit):
            return self.UnitsInRangeOfUnit(u, others, range.sight_range)
        return self.UnitsInRangeOfUnit(u, others, range)

    def GetInRangeEnemyDetectors(self, u: Unit, range: Union[Unit, float]) -> Units:
        enes = self.GetEnemyDetectors()
        if enes.empty:
            return None
        if isinstance(range, Unit):
            return self.UnitsInRangeOfUnit(u, enes, range.sight_range)
        return self.UnitsInRangeOfUnit(u, enes, range)

    # Cancel building on attack
    async def CancelAttackedBuildings(self):
        bot = self.bot
        for s in bot.structures.not_ready:
            if (
                s.build_progress < 1
                and s.build_progress > 0.15
                and s.shield_health_percentage < 0.25
            ):
                enes = self.GetInRangeEnemies(s, 8, self.GetEnemyAmy())
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
            detectors = self.GetInRangeEnemyDetectors(obs, obs)
            if detectors and detectors.amount > 0:
                obs(AbilityId.MORPH_OBSERVERMODE, queue=False)
                # direction = obs.position.offset(bot.start_location)
                direction = obs.position.negative_offset(
                    detectors.closest_n_units(obs, 1).first.position
                )
                obs.move(obs.position + direction.normalized * 8, queue=True)
                continue

            otherObs = self.GetInRangeAllyObs(obs, obs.sight_range - 2)
            if otherObs and otherObs.amount > 0:
                obs(AbilityId.MORPH_OBSERVERMODE, queue=False)
                direction = obs.position.negative_offset(
                    otherObs.closest_n_units(obs, 1).first.position
                )
                obs.move(obs.position + direction.normalized * 6, queue=True)
                continue

            enes = self.GetInRangeEnemies(obs, obs, None)
            if not enes or enes.amount < 3:
                obs(AbilityId.MORPH_OBSERVERMODE, queue=False)

        for ob in bot.units(UnitTypeId.OBSERVER).ready:
            detectors = self.GetInRangeEnemyDetectors(ob, ob)
            if detectors and detectors.amount > 0:
                # direction = obs.position.offset(bot.start_location)
                direction = ob.position.negative_offset(
                    detectors.closest_n_units(ob, 1).first.position
                )
                ob.move(ob.position + direction.normalized * 8)
                continue
            enes = self.GetInRangeEnemies(ob, ob, None)
            otherObs = self.GetInRangeAllyObs(
                ob, ob.sight_range, UnitTypeId.OBSERVERSIEGEMODE
            )
            otherOb = self.GetInRangeAllyObs(ob, ob.sight_range, UnitTypeId.OBSERVER)
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
                retreatPoints: Set[Point2] = self.around8(
                    stalker.position, distance=distanceRetreat
                ) | self.around8(stalker.position, distance=distanceRetreat * 2)
                # Filter points that are pathable
                retreatPoints: Set[Point2] = {
                    x for x in retreatPoints if self.bot.in_pathing_grid(x)
                }
                if retreatPoints:
                    closestEnemy: Unit = enemyThreatsClose.closest_to(stalker)
                    retreatPoint: Unit = closestEnemy.position.furthest(retreatPoints)
                    stalker.move(retreatPoint)
                    return

    # Stolen and modified from position.py
    def around8(self, position, distance=1) -> Set[Point2]:
        p = position
        d = distance
        return self.around4(position, distance) | {
            Point2((p.x - d, p.y - d)),
            Point2((p.x - d, p.y + d)),
            Point2((p.x + d, p.y - d)),
            Point2((p.x + d, p.y + d)),
        }

    # Stolen and modified from position.py
    def around4(self, position, distance=1) -> Set[Point2]:
        p = position
        d = distance
        return {
            Point2((p.x - d, p.y)),
            Point2((p.x + d, p.y)),
            Point2((p.x, p.y - d)),
            Point2((p.x, p.y + d)),
        }

    def GetAllIdleCombatForces(self):
        units: Units = self.bot.units.of_type(
            {
                UnitTypeId.ZEALOT,
                UnitTypeId.SENTRY,
                UnitTypeId.OBSERVER,
                UnitTypeId.STALKER,
                UnitTypeId.IMMORTAL,
                UnitTypeId.ADEPT,
            }
        )
        return units.ready.idle

    def GetAllCombatForces(self):
        units: Units = self.bot.units.of_type(
            {
                UnitTypeId.ZEALOT,
                UnitTypeId.SENTRY,
                UnitTypeId.OBSERVER,
                UnitTypeId.STALKER,
                UnitTypeId.IMMORTAL,
                UnitTypeId.ADEPT,
            }
        )
        return units.ready

    # for AttackPiority
    def GetAttackUnitTypePreference(self, myId: UnitTypeId):
        print("GetAttackUnitTypePreference")

    # for AttackPiority
    def GetAttackTargetPreference(self, u: Unit, rangeAdd: float):
        print("GetAttackTargetPreference")
        lowest_hp = min(in_range_enemies, key=lambda e: (e.health + e.shield, e.tag))
        workers = attackableEnes({UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE})

    async def MicroMoveUnit(
        self, u: Unit, home_location: Point2, enemies_can_attack: Units
    ):
        # TODO chase weak target enemies or hide from enemies
        # only move, no attack
        bot = self.bot
        enemies = self.GetEnemies()
        if not enemies:
            return
        nearestEne: Unit = enemies.closest_to(u)
        dir = u.position.offset(nearestEne.position).normalized
        allies = bot.units.ready.filter(
            lambda unit: not unit == u
            and unit.can_attack
            and unit.type_id
            not in {
                UnitTypeId.EGG,
                UnitTypeId.LARVA,
                UnitTypeId.PROBE,
                UnitTypeId.SCV,
                UnitTypeId.DRONE,
            }
        )
        alliesNearby = self.UnitsInRangeOfUnit(u, allies, 6)
        alliesForceEstimate = 0
        for a in alliesNearby:
            c = bot.calculate_cost(a.type_id)
            alliesForceEstimate += c.minerals + c.vespene
        enesNearby = self.UnitsInRangeOfUnit(nearestEne, enemies, 6)
        enesForceEstimate = 0
        if enesNearby:
            for a in enesNearby:
                c = bot.calculate_cost(a.type_id)
                enesForceEstimate += c.minerals + c.vespene

        # weAreStronger = alliesForceEstimate > enesForceEstimate * 1.5
        # weAreWeaker = alliesForceEstimate * 1 < enesForceEstimate
        weAreStronger = False
        weAreWeaker = False
        if weAreStronger:
            u.move(u.position.towards(nearestEne.position))
        elif weAreWeaker:
            if u.type_id == UnitTypeId.STALKER:
                await self.StalkerEscape(u, home_location, enemies_can_attack)
            else:
                u.move(u.position - dir)
        else:
            if u.type_id == UnitTypeId.STALKER:
                await self.StalkerEscape(u, home_location, enemies_can_attack)

    async def TryAttackNearbyEnemy(self, u: Unit, rangeAdd: float):
        bot = self.bot
        enemies = self.GetEnemies()
        attackableEnes = enemies.in_attack_range_of(u, rangeAdd)
        if not attackableEnes:
            return
        if attackableEnes.amount == 1:
            u.attack(attackableEnes.first)  # closest_n_units
            return
        for e in attackableEnes:
            dmg = u.calculate_damage_vs_target(e)
            if dmg[0] > e.health + e.shield:
                u.attack(e)
                return
        eneToAttackSortedList = sorted(
            attackableEnes,
            key=lambda e: u.calculate_damage_vs_target(e)[0],
            reverse=False,
        )
        u.attack(eneToAttackSortedList[0])

    async def Micro(self):
        bot = self.bot
        enemies = self.GetEnemies()
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

            if u.weapon_cooldown > 0:
                await self.MicroMoveUnit(u, home_location, enemies)
                continue

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
