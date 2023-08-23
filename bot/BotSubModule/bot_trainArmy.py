
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

class bot_trainArmy():
    bot:BotAI
    def __init__(self, bot:BotAI):
        self.bot=bot

    proxyCenter:Unit=None

    def mgRatio(self):
        return  float(self.bot.minerals)/float(self.bot.vespene+0.5)
    
    async def train(self):
        # warp in BG units
        if self.bot.structures(UnitTypeId.WARPGATE).ready.amount>0:
            if self.bot.already_pending_upgrade(UpgradeId.BLINKTECH) > 0 or self.bot.supply_used < 55:
                await self.warp_bg_units(self.bot.structures(UnitTypeId.PYLON).closest_to(self.bot.enemy_start_locations[0]))

        # build VR units
        if self.bot.structures(UnitTypeId.ROBOTICSFACILITY):
            mgRatio = self.mgRatio()
            for vr in self.bot.structures(UnitTypeId.ROBOTICSFACILITY).ready.idle:
                if self.bot.can_afford(UnitTypeId.IMMORTAL) and (mgRatio >= 2 or self.bot.minerals>325):
                    vr.train(UnitTypeId.IMMORTAL)
                elif self.bot.can_afford(UnitTypeId.OBSERVER) and (mgRatio < 0.35 or self.bot.vespene>350):
                    if(self.bot.units(UnitTypeId.OBSERVER).amount + self.bot.units(UnitTypeId.OBSERVERSIEGEMODE).amount) < 1: 
                        vr.train(UnitTypeId.OBSERVER)

    async def warp_bg_units(self, proxy):
        mgRatio = self.mgRatio()
        uid = UnitTypeId.STALKER
        if mgRatio>2.5 and self.bot.vespene<200:
            uid = UnitTypeId.ZEALOT
        if mgRatio<0.4 and self.bot.vespene>200 and self.bot.units(UnitTypeId.SENTRY).amount<3:
            uid = UnitTypeId.SENTRY
        if self.bot.can_afford(uid):
            for warpgate in self.bot.structures(UnitTypeId.WARPGATE).ready:
                abilities = await self.bot.get_available_abilities(warpgate)
                # all the units have the same cooldown anyway so let's just look at STALKER
                if AbilityId.WARPGATETRAIN_STALKER in abilities:
                    pos = proxy.position.to2.random_on_distance(5)
                    placement = await self.bot.find_placement(AbilityId.WARPGATETRAIN_STALKER, pos,7, placement_step=1)
                    if placement is None:
                        # return ActionResult.CantFindPlacementLocation
                        print("can't place")
                        return
                    warpgate.warp_in(uid, placement)

