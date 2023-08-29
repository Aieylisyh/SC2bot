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


class bot_unitSelection:
    bot: BotAI

    def __init__(self, bot: BotAI):
        self.bot = bot

    def GetUnitCostValue(self, u: Unit):
        bot = self.bot
        if not u._creation_ability:
            return 0
        if u.is_hallucination:
            return 0
        if u.type_id in {
            UnitTypeId.LARVA,
            UnitTypeId.EGG,
        }:
            return 0
        c = bot.calculate_cost(u.type_id)
        return c.minerals + c.vespene

    def DamageDealBonusToAjustAttackPriority(self, u: Unit):
        if u.is_hallucination:
            return -100
        if u.is_constructing_scv or u.is_carrying_resource:
            return 10
        if u.type_id in {
            UnitTypeId.LARVA,
        }:
            return -5
        if u.type_id in {
            UnitTypeId.ROACH,
            UnitTypeId.EGG,
        }:
            return -3
        if u.type_id in {
            UnitTypeId.SCV,
            UnitTypeId.PROBE,
            UnitTypeId.MULE,
            UnitTypeId.DRONE,
        }:
            return 5
        if u.type_id in {
            UnitTypeId.SIEGETANK,
            UnitTypeId.SIEGETANKSIEGED,
            UnitTypeId.RAVEN,
            UnitTypeId.GHOST,
            UnitTypeId.HIGHTEMPLAR,
            UnitTypeId.ORACLE,
            UnitTypeId.INFESTOR,
            UnitTypeId.VIPER,
            UnitTypeId.WIDOWMINE,
        }:
            return 4
        if u.type_id in {
            UnitTypeId.MARINE,
            UnitTypeId.DARKTEMPLAR,
            UnitTypeId.COLOSSUS,
            UnitTypeId.BANELING,
            UnitTypeId.DISRUPTOR,
            UnitTypeId.BANSHEE,
            UnitTypeId.WARPPRISM,
            UnitTypeId.MEDIVAC,
            UnitTypeId.OVERLORDTRANSPORT,
            UnitTypeId.QUEEN,
            # TODO
        }:
            return 2
        return 0

    def GetUnitPowerValue(self, u: Unit):
        bot = self.bot
        if u.type_id in {
            UnitTypeId.SCV,
            UnitTypeId.PROBE,
            UnitTypeId.MULE,
            UnitTypeId.DRONE,
        }:
            return 20
        return self.GetUnitCostValue(u)

    def FilterAttack(
        self,
        units: Units,
        allowNoAtk: bool = False,
        allowNoAtkGround: bool = True,
        allowNoAtkAir: bool = True,
    ):
        if not allowNoAtk:
            units = units.filter(lambda unit: unit.can_attack)
        if not allowNoAtkGround:
            units = units.filter(lambda unit: unit.can_attack_ground)
        if not allowNoAtkAir:
            units = units.filter(lambda unit: unit.can_attack_air)

        return units

    def FilterDetectors(self, units: Units):
        units = units.filter(lambda unit: unit.is_detector)
        return units

    def FilterCloaked(self, units: Units, allowRevealed: bool = True):
        units = units.filter(lambda unit: unit.is_cloaked)
        if not allowRevealed:
            units = units.filter(lambda unit: not unit.is_revealed)
        return units

    def GetUnits(
        self,
        EneOrAlly: bool,
        ground: bool = True,
        air: bool = True,
        workers: bool = False,
        misc: bool = False,
    ):
        bot = self.bot
        # TODO Bug that void Ray has no weapon!
        units: Units
        if EneOrAlly:
            units = bot.enemy_units
        else:
            units = bot.units
        if not misc:
            units = units.filter(
                lambda unit: unit.type_id
                not in {
                    UnitTypeId.LARVA,
                    UnitTypeId.EGG,
                    UnitTypeId.MULE,
                    UnitTypeId.NUKE,
                }
                and not unit.is_hallucination
            )
        if not workers:
            units = units.filter(
                lambda unit: unit.type_id
                not in {
                    UnitTypeId.SCV,
                    UnitTypeId.PROBE,
                    UnitTypeId.MULE,
                    UnitTypeId.DRONE,
                }
            )
        if not ground:
            units = units.filter(lambda unit: unit.is_flying)
        if not air:
            units = units.filter(lambda unit: not unit.is_flying)

        return units

    def GetAttackableStructures(self, structures: Units):
        return structures.filter(
            lambda s: (
                s.type_id
                in {
                    UnitTypeId.BUNKER,
                    UnitTypeId.MISSILETURRET,
                    UnitTypeId.SPINECRAWLER,
                    UnitTypeId.SPORECANNON,
                    UnitTypeId.PHOTONCANNON,
                    UnitTypeId.PLANETARYFORTRESS,
                }
            )
        )

    def UnitsInRangeOfUnit(self, u: Unit, us: Units, range: float) -> Units:
        return us.filter(
            lambda v: self.bot._distance_squared_unit_to_unit(u, v) < range * range
        )

    def GetInRangeUnits(self, u: Unit, range: Union[Unit, float], units: Units):
        if units.empty:
            return None
        if isinstance(range, Unit):
            return self.UnitsInRangeOfUnit(u, units, range.sight_range)
        return self.UnitsInRangeOfUnit(u, units, range)

    def GetInRangeAllyObservers(
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
        enes = self.GetUnits(EneOrAlly=True)
        enes = self.FilterDetectors(enes)
        if enes.empty:
            return None
        if isinstance(range, Unit):
            return self.UnitsInRangeOfUnit(u, enes, range.sight_range)
        return self.UnitsInRangeOfUnit(u, enes, range)

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
