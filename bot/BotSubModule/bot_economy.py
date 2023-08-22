
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

class bot_economy():
    bot:StalkerRush.StalkerRushBot
    def __init__(self, bot:BotAI):
        self.bot=bot
    
    supply_nexus=15
    supply_pylon=8
    mineralFieldCount=8
    vespineGasCount=2

    target_MineralGas_Ratio:float=1.5
    target_Base_Count:int=3
    target_BG_Count:int=3

    @property
    def workerCapPerTownhall(self):
        return self.mineralFieldCount*2+self.vespineGasCount*3
        

    def GetSupplyCap(self, includingPending):
        if(includingPending):
            return self.bot.buildStructure.GetBuildingCount(UnitTypeId.NEXUS)*self.supply_nexus + self.bot.buildStructure.GetBuildingCount(UnitTypeId.PYLON)*self.supply_pylon
        return self.bot.supply_cap
    
    async def TrainWorkers(self):
        if not self.bot.can_afford(UnitTypeId.PROBE):
            return
        townhalls = self.bot.townhalls.ready.idle
        targetWorker = min(townhalls.amount * self.workerCapPerTownhall, self.GetSupplyCap(True))
        for townhall in townhalls:
            if self.bot.supply_workers + self.bot.already_pending(UnitTypeId.PROBE) < targetWorker:
                await townhall.train(UnitTypeId.PROBE)

    #Build gas assimilators
    async def Buildassimilators(self):
    #Our distribute workers method will then assign workers to the gas
        #assimilatorCount = self.bot.buildStructure.GetBuildingCount(UnitTypeId.ASSIMILATOR)
        townhalls = self.bot.townhalls.ready
        probes = self.bot.units(UnitTypeId.PROBE)
        if(probes.amount>=townhalls.amount*self.mineralFieldCount*2-1):
            #build 1 assimilator
            await self.BuildAssimilator(townhalls,1)
        if(probes.amount>=townhalls.amount*self.mineralFieldCount*2+2):
            #build 1 assimilator
            await self.BuildAssimilator(townhalls,1)
    
    async def BuildAssimilator(self, townhalls:Units, amount:int):   
        if not self.bot.can_afford(UnitTypeId.ASSIMILATOR):
            return
        for townhall in townhalls:
            vgs = self.bot.vespene_geyser.closer_than(15, townhall)
            for vg in vgs:
                assimilatorCount = self.bot.gas_buildings.closer_than(1, vg).amount
                if(assimilatorCount>=amount):
                    break
                worker = self.bot.select_build_worker(vg.position)
                if worker is None:
                    break
                await worker.build(UnitTypeId.ASSIMILATOR, vg)
                worker.stop(queue=True)
