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

    def __init__(self, bot: BotAI):
        self.bot = bot
        self.scouts_and_spots = {}
        self.scoutTargetIndex = 0

    def GetEnemies(self) -> Units:
        bot = self.bot
        return bot.enemy_units.filter(
            lambda unit: unit.type_id not in {UnitTypeId.LARVA, UnitTypeId.EGG}
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

    def GetInRangeEnemies(self, u: Unit, range: Union[Unit, float]) -> Units:
        enes = self.GetEnemies()
        if enes.empty:
            return None
        if isinstance(range, Unit):
            return self.UnitsInRangeOfUnit(u, enes, range.sight_range)
        return self.UnitsInRangeOfUnit(u, enes, range)

    def GetInRangeEnemyAmy(self, u: Unit, range: Union[Unit, float]) -> Units:
        enes = self.GetEnemyAmy()
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

    def GetInRangeDetectors(self, u: Unit, range: Union[Unit, float]) -> Units:
        enes = self.GetEnemyDetectors()
        if enes.empty:
            return None
        if isinstance(range, Unit):
            return self.UnitsInRangeOfUnit(u, enes, range.sight_range)
        return self.UnitsInRangeOfUnit(u, enes, range)

    async def scout_ob(self):
        # Method to send our obs scouting
        # We retrieve the list of possible extensions
        bot = self.bot
        self.ordered_expansions = None
        self.ordered_expansions = sorted(
            # You are using 'self.expansion_locations', please use 'self.expansion_locations_list' (fast) or 'self.expansion_locations_dict' (slow) instead.
            bot.expansion_locations_list,
            key=lambda expansion: expansion.distance_to(bot.enemy_start_locations[0]),
        )
        # MORPH_OBSERVERMODE = 3739
        # MORPH_SURVEILLANCEMODE = 3741
        for obs in bot.units(UnitTypeId.OBSERVERSIEGEMODE).ready:
            detectors = self.GetInRangeDetectors(obs, obs)
            if detectors and detectors.amount > 0:
                obs(AbilityId.MORPH_OBSERVERMODE, queue=False)
                direction = obs.position.offset(bot.start_location)
                obs.move(obs.position + direction.normalized * 8, queue=True)
                continue

            otherObs = self.GetInRangeAllyObs(obs, obs.sight_range - 1.5)
            if otherObs and otherObs.amount > 0:
                obs(AbilityId.MORPH_OBSERVERMODE, queue=False)
                direction = obs.position.negative_offset(
                    otherObs.closest_n_units(obs, 1).first.position
                )
                obs.move(obs.position + direction.normalized * 6, queue=True)
                continue

            enes = self.GetInRangeEnemies(obs, obs)
            if not enes or enes.amount < 3:
                obs(AbilityId.MORPH_OBSERVERMODE, queue=False)

        for ob in bot.units(UnitTypeId.OBSERVER).ready:
            detectors = self.GetInRangeDetectors(ob, ob)
            if detectors and detectors.amount > 0:
                direction = ob.position.offset(bot.start_location)
                ob.move(ob.position + direction.normalized * 8)
                continue
            enes = self.GetInRangeEnemies(ob, ob)
            otherObs = self.GetInRangeAllyObs(ob, ob.sight_range)
            otherOb = self.GetInRangeAllyObs(ob, ob.sight_range, UnitTypeId.OBSERVER)
            if enes and enes.amount > 4 and not otherObs and not otherOb:
                ob(AbilityId.MORPH_SURVEILLANCEMODE, queue=False)
                continue
            if ob.is_idle:
                # scout
                sorted_expansion_locations_list: list = sorted(
                    bot.expansion_locations_list,
                    key=lambda el: el.distance_to(bot.enemy_start_locations[0]),
                    reverse=False,
                )
                maxIndex = 2
                if len(sorted_expansion_locations_list) < 4:
                    maxIndex = 0
                elif len(sorted_expansion_locations_list) < 6:
                    maxIndex = 1
                targetLocation = sorted_expansion_locations_list[self.scoutTargetIndex]
                self.scoutTargetIndex += 1
                if self.scoutTargetIndex > maxIndex:
                    self.scoutTargetIndex = 0
                ob.move(targetLocation)

    # Our method to micro and to blink
    async def micro(self):
        home_location = self.bot.start_location
        enemies = self.bot.enemy_units.filter(
            lambda unit: unit.type_id not in {UnitTypeId.DRONE, UnitTypeId.SCV}
        )
        enemies_can_attack: Units = enemies.filter(lambda unit: unit.can_attack_ground)
        for stalker in self.bot.units(UnitTypeId.STALKER).ready:
            escape_location = stalker.position.towards(home_location, 6)
            enemyThreatsClose: Units = enemies_can_attack.filter(
                lambda unit: unit.distance_to(stalker) < 15
            )  # Threats that can attack the stalker
            if stalker.shield < 10 and enemyThreatsClose:
                abilities = await self.bot.get_available_abilities(stalker)
                if AbilityId.EFFECT_BLINK_STALKER in abilities:
                    # await self.bot.order(stalker, EFFECT_BLINK_STALKER, escape_location)
                    stalker(AbilityId.EFFECT_BLINK_STALKER, escape_location)
                    continue
                else:
                    retreatPoints: Set[Point2] = self.around8(
                        stalker.position, distance=2
                    ) | self.around8(stalker.position, distance=4)
                    # Filter points that are pathable
                    retreatPoints: Set[Point2] = {
                        x for x in retreatPoints if self.bot.in_pathing_grid(x)
                    }
                    if retreatPoints:
                        closestEnemy: Unit = enemyThreatsClose.closest_to(stalker)
                        retreatPoint: Unit = closestEnemy.position.furthest(
                            retreatPoints
                        )
                        stalker.move(retreatPoint)
                        continue  # Continue for loop, dont execute any of the following

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

    def GetAllCombatForces(self):
        units: Units = self.bot.units.of_type(
            {
                UnitTypeId.ZEALOT,
                UnitTypeId.SENTRY,
                UnitTypeId.OBSERVER,
                UnitTypeId.STALKER,
                UnitTypeId.IMMORTAL,
            }
        )
        return units.ready.idle
