
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
from bot import StalkerRush
class bot_proxyUnits():
    bot:StalkerRush.StalkerRushBot
    def __init__(self, bot:BotAI):
        self.bot=bot

    proxyCenter:Unit=None

    async def warp_bg_units(self, proxy):
        mgRatio = float(self.minerals)/float(self.vespene+0.5)
        uid = UnitTypeId.STALKER
        if mgRatio>2.5 and self.vespene<200:
            uid = UnitTypeId.ZEALOT
        if mgRatio<0.4 and self.vespene>200 and self.units(UnitTypeId.SENTRY).amount<3:
            uid = UnitTypeId.SENTRY
        if self.can_afford(uid):
            for warpgate in self.structures(UnitTypeId.WARPGATE).ready:
                abilities = await self.get_available_abilities(warpgate)
                # all the units have the same cooldown anyway so let's just look at STALKER
                if AbilityId.WARPGATETRAIN_STALKER in abilities:
                    pos = proxy.position.to2.random_on_distance(5)
                    placement = await self.find_placement(AbilityId.WARPGATETRAIN_STALKER, pos,7, placement_step=1)
                    if placement is None:
                        # return ActionResult.CantFindPlacementLocation
                        print("can't place")
                        return
                    warpgate.warp_in(uid, placement)

