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


class bot_nexusSkill:
    bot: BotAI

    def __init__(self, bot: BotAI):
        self.bot = bot

    def mostEnergy(self, units: Units) -> Unit:
        return max(
            (u for u in units),
            key=lambda unit: unit.energy,
        )

    def IsValidChronoBoostTarget(self, u: Unit):
        if not u or u.is_idle or u.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
            return False
        if u.orders[0].progress > 0.9:
            return False
        return True

    # Method for Chrono boost
    async def ChronoBoost(self):
        bot = self.bot
        nexus = self.mostEnergy(bot.townhalls.ready)
        if not nexus:
            return
        if nexus.energy < 50:
            return
        # print(nexus.energy)
        abId = AbilityId.EFFECT_CHRONOBOOSTENERGYCOST
        # We get the list of our buildings that we want to chronoboost
        BY: Unit = None
        BF: Unit = None
        VC: Unit = None
        if bot.structures(UnitTypeId.CYBERNETICSCORE).ready:
            BY = bot.structures(UnitTypeId.CYBERNETICSCORE).ready.first
        if bot.structures(UnitTypeId.FORGE).ready:
            BF = bot.structures(UnitTypeId.FORGE).ready.first
        if bot.structures(UnitTypeId.TWILIGHTCOUNCIL).ready:
            VC = bot.structures(UnitTypeId.TWILIGHTCOUNCIL).ready.first

        if self.IsValidChronoBoostTarget(BY):
            nexus(abId, BY)
            return
        if self.IsValidChronoBoostTarget(VC):
            nexus(abId, VC)
            return
        if self.IsValidChronoBoostTarget(BF):
            nexus(abId, BF)
            return

        # finally the nexus if we are under 70 probes
        if bot.workers.amount < 70 and bot.workers.amount > 13 and nexus.energy >= 75:
            for n in bot.townhalls.ready:
                if self.IsValidChronoBoostTarget(n):
                    nexus(abId, n)
                    return

        if bot.workers.amount > 22:
            # and then the vr vs warpgates
            vrs = bot.structures(UnitTypeId.ROBOTICSFACILITY).ready
            if vrs:
                for vr in vrs:
                    if (
                        self.IsValidChronoBoostTarget(vr)
                        and vr.orders[0].progress < 0.5
                    ):
                        nexus(abId, vr)
                        return

            vss = bot.structures(UnitTypeId.STARGATE).ready
            if vss:
                for vs in vss:
                    if (
                        self.IsValidChronoBoostTarget(vs)
                        and vs.orders[0].progress < 0.5
                    ):
                        nexus(abId, vs)
                        return

            warpgates = bot.structures(UnitTypeId.WARPGATE).ready
            if warpgates:
                for warpgate in warpgates:
                    if (
                        self.IsValidChronoBoostTarget(warpgate)
                        and warpgate.orders[0].progress < 0.3
                    ):
                        nexus(abId, warpgate)
                        return
