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

from bot.BotSubModule.bot_buildStructure import bot_buildStructure
from bot.BotSubModule.bot_economy import bot_economy
from bot.BotSubModule.bot_mainStrategy import bot_mainStrategy
from bot.BotSubModule.bot_tactics import bot_tactics
from bot.BotSubModule.bot_unitSelection import bot_unitSelection
from bot.BotSubModule.bot_proxyUnits import bot_proxyUnits
from bot.BotSubModule.bot_nexusSkill import bot_nexusSkill
from bot.BotSubModule.bot_tech import bot_tech

# learn source：https://brax.gg/python-sc2-advanced-bot/

class StalkerRushBot(BotAI):
  NAME: str = "StalkerRush"
  RACE: Race = Race.Protoss

  iter3:int =0
  iter10:int =0

  buildStructure:bot_buildStructure
  economy:bot_economy
  mainStrategy:bot_mainStrategy
  tactics:bot_tactics
  tech:bot_tech
  unitSelection:bot_unitSelection
  proxyUnits:bot_proxyUnits
  nexusSkill:bot_nexusSkill

  def AttackWithAllForces(self):
    all_attack_units = bot_unitSelection.all_units(self)
    t = self.enemy_start_locations[0]
    for unit in all_attack_units:
        if unit.can_attack:
          unit.attack(t)

  async def DoIter10(self):
    self.iter10+=1
    
  async def DoIter3(self):
    self.iter3+=1
    await self.economy.BuildAssimilators()
    await self.economy.DistributeWorkers()
    #print("DoIter3")


  def LaunchAttack(self):
    if self.already_pending_upgrade(UpgradeId.BLINKTECH) <0.9:
       return
    
    myForces = self.GetAllCombatForces()
    if myForces.amount> self.attackForce_count:
      #targets = (self.enemy_units | self.enemy_structures).filter(lambda unit: unit.can_be_attacked)
      target=self.enemy_start_locations[0].position
      for f in myForces.idle:
        if f.can_attack:
          f.attack(target)
        else:
          f.move(target)
    return

 
  async def on_start(self):
      print("StalkerRushBot Game started")
      self.buildStructure= bot_buildStructure(self)
      self.economy= bot_economy(self)
      self.mainStrategy= bot_mainStrategy(self)
      self.tactics= bot_tactics(self)
      self.tech= bot_tech(self)
      self.unitSelection= bot_unitSelection(self)
      self.proxyUnits= bot_proxyUnits(self)
      self.nexusSkill= bot_nexusSkill(self)

      await self.economy.DistributeWorkers(True)


  async def on_end(self, result):
      print("Game ended.")
      print(str(result))

  async def on_step(self, iteration):
    if not self.townhalls.ready:
      self.AttackWithAllForces()
      return
    
    if(iteration%10==0):
      await self.DoIter10()
    if(iteration%3==0):
      await self.DoIter3()
      
    if(iteration==0):
      await self.chat_send("(glhf)")

    await self.tactics.micro()
    await self.tech.forge_research()
    await self.buildStructure.build_productions()
    await self.economy.TrainWorkers()

    return
  
    # warp in BG units
    if self.structures(UnitTypeId.WARPGATE).ready.amount>0:
      if self.already_pending_upgrade(UpgradeId.BLINKTECH) >0 or self.supply_used < 67:
        await self.warp_bg_units(self.structures(UnitTypeId.PYLON).closest_to(self.enemy_start_locations[0]))

    # build VR units
    if self.structures(UnitTypeId.ROBOTICSFACILITY):
      mgRatio = float(self.minerals)/float(self.vespene+0.5)
      for vr in self.structures(UnitTypeId.ROBOTICSFACILITY).ready.idle:
        if self.can_afford(UnitTypeId.IMMORTAL) and (mgRatio >= 2 or self.minerals>325):
          vr.train(UnitTypeId.IMMORTAL)
        elif self.can_afford(UnitTypeId.OBSERVER) and (mgRatio < 0.35 or self.vespene>350):
          if(self.units(UnitTypeId.OBSERVER).amount + self.units(UnitTypeId.OBSERVERSIEGEMODE).amount) < 1: 
            vr.train(UnitTypeId.OBSERVER)

    if(not self.nexus2 and self.structures.ready(UnitTypeId.NEXUS).amount==1 and self.structures(UnitTypeId.NEXUS).amount==2):
      #nexus2 assign
      print("nexus2 assign")
      self.nexus2 = self.structures.not_ready(UnitTypeId.NEXUS).first
    
    # If we are low on supply, build pylon
    supplyUsed = self.supply_used
    pylonCount = self.structures(UnitTypeId.PYLON).ready.amount + self.already_pending(UnitTypeId.PYLON) 
    supply_left_expected = self.supply_left + self.already_pending(UnitTypeId.PYLON)*8
    if (
        pylonCount == 0
        or supplyUsed > 185 and supply_left_expected < 5
        or supplyUsed > 100 and supply_left_expected < 9 
        or supplyUsed > 64 and supply_left_expected < 7
        or supplyUsed > 26 and supply_left_expected < 5 
        or supplyUsed > 18 and supply_left_expected < 4 
        or pylonCount < 2 and supply_left_expected < 5
    ):
        # Always check if you can afford something before you build it
        if self.can_afford(UnitTypeId.PYLON):
            print("build PYLON pylon/supplyUsed:"+str(pylonCount)+"/"+str(supplyUsed))
            #print(self.main_base_ramp.protoss_wall_pylon)
            #print(self.structures(UnitTypeId.PYLON).amount)
            #print(self.structures(UnitTypeId.PYLON).ready.amount)
            #print(self.already_pending(UnitTypeId.PYLON))
            if pylonCount==0:
              await self.build(UnitTypeId.PYLON, self.main_base_ramp.protoss_wall_pylon, 3)
            elif pylonCount==1:
              if self.townhalls.amount>=2:
                if self.buildingsCenter == None:
                  self.buildingsCenter = self.structures(UnitTypeId.PYLON)[0]
                # direction up the ramp
                print("build PYLON2")
                direction = nexus.position.negative_offset(self.buildingsCenter.position)
                #print(str(direction))
                #print(str(nexus.position))
                #print(str(self.buildingsCenter.position))
                await self.build(UnitTypeId.PYLON,  self.buildingsCenter.position + 0.5 * direction, 3)
            else:
              if(pylonCount%2==0 and self.nexus2):
                print("build pylon near nexus 2")
                await self.build(UnitTypeId.PYLON, self.nexus2, 15)
              else:
                await self.build(UnitTypeId.PYLON, self.buildingsCenter, pylonCount*2 + 20)

    # Train probe on nexuses that are undersaturated (avoiding distribute workers functions)
    # if nexus.assigned_harvesters < nexus.ideal_harvesters and nexus.is_idle:

    if self.structures(UnitTypeId.PYLON).ready and self.supply_workers + self.already_pending(UnitTypeId.PROBE) < self.townhalls.amount * 22 and nexus.is_idle:
        if self.can_afford(UnitTypeId.PROBE):
          nexus.train(UnitTypeId.PROBE)
    else:
        if self.supply_workers + self.already_pending(UnitTypeId.PROBE) <= min(22,self.townhalls.amount * 12 + pylonCount * 8) and nexus.is_idle:
          if self.can_afford(UnitTypeId.PROBE):
            nexus.train(UnitTypeId.PROBE)
    
    # expand base
    if (self.townhalls.ready.amount + self.already_pending(UnitTypeId.NEXUS) < self.target_base_count
        and self.supply_workers  >= self.townhalls.amount * 20-2
      ):
        if self.can_afford(UnitTypeId.NEXUS):
            await self.expand_now()

    # Once we have a pylon completed
    if self.structures(UnitTypeId.PYLON).ready:
        if self.structures(UnitTypeId.GATEWAY).ready and self.townhalls.ready.amount + self.already_pending(UnitTypeId.NEXUS) > 1:
          # If we have gateway completed, build cyber core
          if not self.structures(UnitTypeId.CYBERNETICSCORE):
              if (
                  self.can_afford(UnitTypeId.CYBERNETICSCORE)
                  and self.already_pending(UnitTypeId.CYBERNETICSCORE) == 0
              ):
                  await self.build(UnitTypeId.CYBERNETICSCORE, near=self.buildingsCenter)
          else:
            # build VC
            if self.already_pending_upgrade(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1) >0 and self.can_afford(UnitTypeId.TWILIGHTCOUNCIL) and self.structures(UnitTypeId.TWILIGHTCOUNCIL).amount == 0 and self.already_pending(UnitTypeId.TWILIGHTCOUNCIL) == 0:
                await self.build(UnitTypeId.TWILIGHTCOUNCIL, near=self.buildingsCenter)
            # build BF
            if self.structures(UnitTypeId.ROBOTICSFACILITY) and self.can_afford(UnitTypeId.FORGE) and self.structures(UnitTypeId.FORGE).ready.amount == 0 and self.already_pending(UnitTypeId.FORGE) == 0:
                await self.build(UnitTypeId.FORGE, near=self.buildingsCenter)
        else:
          # If we have no gateway, build gateway
          if self.can_afford(UnitTypeId.GATEWAY) and self.structures(UnitTypeId.GATEWAY).ready.amount==0 and self.already_pending(UnitTypeId.GATEWAY) == 0:
              await self.build(UnitTypeId.GATEWAY, near=self.buildingsCenter)
    
    # build more BG
    if self.structures(UnitTypeId.PYLON).ready and self.structures(UnitTypeId.CYBERNETICSCORE).ready:
        bgCount = (self.structures(UnitTypeId.GATEWAY).ready.amount + self.already_pending(UnitTypeId.GATEWAY) + self.structures(UnitTypeId.WARPGATE).ready.amount + self.already_pending(UnitTypeId.WARPGATE))
        
        if(bgCount>=2):
          if self.can_afford(UnitTypeId.ROBOTICSFACILITY) and self.structures(UnitTypeId.ROBOTICSFACILITY).amount==0 and self.already_pending(UnitTypeId.ROBOTICSFACILITY) == 0:
            await self.build(UnitTypeId.ROBOTICSFACILITY, near=self.buildingsCenter)

        if (self.townhalls.ready.amount >= self.target_base_count):
          if (bgCount < self.target_bg_count):
            if self.can_afford(UnitTypeId.GATEWAY):
                print("build bg to max "+str(bgCount))
                await self.build(UnitTypeId.GATEWAY, near=self.buildingsCenter)
        else:
          if (bgCount < self.townhalls.ready.amount*2):
            if self.can_afford(UnitTypeId.GATEWAY):
                print("build bg to keep min "+str(bgCount))
                await self.build(UnitTypeId.GATEWAY, near=self.buildingsCenter)

    # Build gas near completed nexuses once we have a cybercore (does not need to be completed
    if self.structures(UnitTypeId.CYBERNETICSCORE).ready and self.structures(UnitTypeId.ASSIMILATOR).ready.amount==0 and self.already_pending(UnitTypeId.ASSIMILATOR)==0:
        for nexus in self.townhalls.ready:
            vgs = self.vespene_geyser.closer_than(15, nexus)
            for vg in vgs:
                if not self.can_afford(UnitTypeId.ASSIMILATOR):
                    break

                worker = self.select_build_worker(vg.position)
                if worker is None:
                    break

                if not self.gas_buildings or not self.gas_buildings.closer_than(1, vg):
                    worker.build_gas(vg)
                    worker.stop(queue=True)
    if self.structures(UnitTypeId.CYBERNETICSCORE):
        for nexus in self.townhalls.ready:
            vgs = self.vespene_geyser.closer_than(15, nexus)
            for vg in vgs:
                if not self.can_afford(UnitTypeId.ASSIMILATOR):
                    break

                worker = self.select_build_worker(vg.position)
                if worker is None:
                    break

                if not self.gas_buildings or not self.gas_buildings.closer_than(1, vg):
                    worker.build_gas(vg)
                    worker.stop(queue=True)