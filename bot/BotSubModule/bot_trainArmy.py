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


class bot_trainArmy:
    bot: BotAI

    def __init__(self, bot: BotAI):
        self.bot = bot

    proxyCenter: Unit = None

    def mgRatio(self):
        return float(self.bot.minerals) / float(self.bot.vespene + 0.5)

    async def train(self):
        bot = self.bot
        townhallAmount = bot.townhalls.amount
        if (
            bot.startingGame_stalkersBuilt < 2
            and bot.structures(UnitTypeId.GATEWAY).ready
            and bot.structures(UnitTypeId.CYBERNETICSCORE).ready
        ):
            for bg in bot.structures(UnitTypeId.GATEWAY).ready:
                if bg.is_idle and bot.can_afford(UnitTypeId.STALKER):
                    bg.train(UnitTypeId.STALKER)
                    bot.startingGame_stalkersBuilt += 1

        # warp in BG units
        if bot.structures(UnitTypeId.WARPGATE).ready.amount > 0:
            if (
                bot.already_pending_upgrade(UpgradeId.BLINKTECH) > 0
                or bot.supply_used < 55
            ):
                await self.warp_bg_units(
                    bot.structures(UnitTypeId.PYLON).closest_to(
                        bot.enemy_start_locations[0]
                    )
                )

        # build VR units
        if bot.structures(UnitTypeId.ROBOTICSFACILITY):
            mgRatio = self.mgRatio()
            for vr in bot.structures(UnitTypeId.ROBOTICSFACILITY).ready.idle:
                if (
                    bot.can_afford(UnitTypeId.IMMORTAL)
                    and (mgRatio >= 1.8 or bot.minerals > 300)
                    and bot.units(UnitTypeId.IMMORTAL).amount < townhallAmount + 1
                    and bot.units(UnitTypeId.OBSERVER).amount
                    + bot.units(UnitTypeId.OBSERVERSIEGEMODE).amount
                    > 1
                ):
                    vr.train(UnitTypeId.IMMORTAL)
                elif bot.can_afford(UnitTypeId.OBSERVER) and (
                    mgRatio < 0.4 or bot.vespene > 300
                ):
                    if (
                        bot.units(UnitTypeId.OBSERVER).amount
                        + bot.units(UnitTypeId.OBSERVERSIEGEMODE).amount
                    ) < townhallAmount * 1.5 - 0.5:
                        vr.train(UnitTypeId.OBSERVER)

    async def warp_bg_units(self, proxy: Unit):
        bot = self.bot
        mgRatio = self.mgRatio()
        uid = UnitTypeId.STALKER
        townhallAmount = bot.townhalls.amount
        if (
            mgRatio > 1.5
            and bot.units(UnitTypeId.ZEALOT).amount < 4 * townhallAmount - 1
        ) or (
            mgRatio > 2.5 and bot.units(UnitTypeId.ZEALOT).amount < 5 * townhallAmount
        ):
            uid = UnitTypeId.ZEALOT
        if (
            mgRatio < 0.4
            and bot.vespene > 200
            and bot.units(UnitTypeId.SENTRY).amount < townhallAmount + 1
        ):
            uid = UnitTypeId.SENTRY
        if mgRatio > 1.2 and bot.units(UnitTypeId.ADEPT).amount < 2:
            uid = UnitTypeId.ADEPT

        if bot.can_afford(uid):
            for warpgate in bot.structures(UnitTypeId.WARPGATE).ready:
                abilities = await bot.get_available_abilities(warpgate)
                # all the units have the same cooldown anyway so let's just look at STALKER
                if AbilityId.WARPGATETRAIN_STALKER in abilities:
                    pos = proxy.position.to2.random_on_distance(5)
                    placement = await bot.find_placement(
                        AbilityId.WARPGATETRAIN_STALKER, pos, 7, placement_step=1
                    )
                    if placement is None:
                        # return ActionResult.CantFindPlacementLocation
                        # print("can't place")
                        return
                    warpgate.warp_in(uid, placement)
