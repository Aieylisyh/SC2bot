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
#import string

from bot.BotSubModule.botEnums.LocationPref import LocationPref

class bot_buildStructure(BotAI):
    bot:BotAI

    def __init__(self, bot:BotAI):
        self.bot=bot

    target_MineralGas_Ratio:float=1.5
    target_Base_Count:int=3
    target_BG_Count:int=3

    nexus2:Unit=None
    base2MainPylon:Unit=None
    base1MainPylon:Unit=None

    def GetBuildingCount(self, id:UnitTypeId, ready:bool =True, building:bool=True, pending:bool=True):
        if(id == UnitTypeId.NOTAUNIT):
            return 0
        
        b110 = self.bot.structures(id).amount
        b100 = self.bot.structures(id).ready.amount
        b011 = self.bot.already_pending(id)
        if(ready and building and pending):
            return b100+b011
        if(ready and building and not pending):
            return b110
        if(ready and not building and pending):
            return b100*2+b011-b110
        if(ready and not building and not pending):
            return b100
        if(not ready and building and pending):
            return b011
        if(not ready and building and not pending):
            return b110-b100
        if(not ready and not building and pending):
            return b011+b100-b110
        if(not ready and not building and not pending):
            return 0

    async def buildOne(self, id:UnitTypeId, minAmount:int, near:Unit|Point2, maxDistance=20,
                        dependId:UnitTypeId= UnitTypeId.NOTAUNIT, dependProgress:float=0,
                        subId1:UnitTypeId= UnitTypeId.NOTAUNIT, subId2:UnitTypeId= UnitTypeId.NOTAUNIT, subId3:UnitTypeId= UnitTypeId.NOTAUNIT,
                        subDependId1:UnitTypeId= UnitTypeId.NOTAUNIT, subDependId2:UnitTypeId= UnitTypeId.NOTAUNIT, subDependId3:UnitTypeId= UnitTypeId.NOTAUNIT):
        if(not self.bot.can_afford(id)):
            return
        
        amount =self.GetBuildingCount(id)
        amount+=self.GetBuildingCount(subId1)
        amount+=self.GetBuildingCount(subId2)
        amount+=self.GetBuildingCount(subId3)

        if(amount>=minAmount):
            return
        hasDepend = True
        if(dependProgress>0 and not dependId == UnitTypeId.NOTAUNIT):
            dependAmount =self.GetBuildingCount(dependId)
            dependAmount+=self.GetBuildingCount(subDependId1)
            dependAmount+=self.GetBuildingCount(subDependId2)
            dependAmount+=self.GetBuildingCount(subDependId3)
            hasDepend = dependAmount >= dependProgress
        if(hasDepend):
            await self.bot.build(id, near=near)

    #Build production buildings
    async def build_productions(self):
        #print("build pylon 1")
        await self.buildOne(UnitTypeId.PYLON,1, self.bot.main_base_ramp.protoss_wall_pylon,2)
        if not self.base1MainPylon and self.bot.structures(UnitTypeId.PYLON).ready:
            self.base1MainPylon = self.bot.structures(UnitTypeId.PYLON).closest_to(self.bot.main_base_ramp.protoss_wall_pylon)
        if self.base1MainPylon:
            pylon = self.base1MainPylon
            #BG 1
            await self.buildOne(UnitTypeId.GATEWAY,1, pylon,UnitTypeId.PYLON,1,subDependId1=UnitTypeId.WARPGATE)
            #BA 1
            await self.buildOne(UnitTypeId.ASSIMILATOR,1, pylon,UnitTypeId.PYLON,1,subDependId1=UnitTypeId.WARPGATE)
            #BY 1
            await self.buildOne(UnitTypeId.CYBERNETICSCORE,1, pylon,UnitTypeId.GATEWAY,1,subDependId1=UnitTypeId.WARPGATE)
            #BG 2
            await self.buildOne(UnitTypeId.GATEWAY,2, pylon,UnitTypeId.GATEWAY,1,subDependId1=UnitTypeId.WARPGATE)

            #We build a twilight councul when we have at least 2 gates and an expend
            if (
                self.bot.can_afford(UnitTypeId.TWILIGHTCOUNCIL)
                and self.bot.structures(UnitTypeId.WARPGATE).amount + self.bot.structures(UnitTypeId.GATEWAY).amount > 2 
                and not self.bot.structures(UnitTypeId.TWILIGHTCOUNCIL)
                and self.bot.already_pending(UnitTypeId.TWILIGHTCOUNCIL) == 0
                and  self.bot.structures(UnitTypeId.NEXUS).amount > 1
            ):
                await self.bot.build(UnitTypeId.TWILIGHTCOUNCIL, near=pylon)					
            #We build a forge when we have at least 2 gates and an expend
            elif (
                self.bot.can_afford(UnitTypeId.FORGE)
                and self.bot.structures(UnitTypeId.WARPGATE).amount + self.bot.structures(UnitTypeId.GATEWAY).amount > 2 
                and not self.bot.structures(UnitTypeId.FORGE)
                and  self.bot.structures(UnitTypeId.CYBERNETICSCORE).ready.amount == 1
                and self.bot.already_pending(UnitTypeId.FORGE) == 0
                and  self.bot.structures(UnitTypeId.NEXUS).amount > 1
            ):
                await self.bot.build(UnitTypeId.FORGE, near=pylon)	
            #We build to 7 gates when we have an expend
            elif (
                self.bot.can_afford(UnitTypeId.GATEWAY)
                and self.bot.structures(UnitTypeId.WARPGATE).amount + self.bot.structures(UnitTypeId.GATEWAY).amount < 7
                and self.bot.structures(UnitTypeId.NEXUS).amount > 1
            ):
                await self.bot.build(UnitTypeId.GATEWAY, near=pylon)
            #We build a robotics facility when we have an expend
            elif (
                self.bot.can_afford(UnitTypeId.ROBOTICSFACILITY)
                and self.bot.structures(UnitTypeId.ROBOTICSFACILITY).amount  < 1
                and self.bot.structures(UnitTypeId.NEXUS).amount > 1
            ):
                await self.bot.build(UnitTypeId.ROBOTICSFACILITY, near=pylon)