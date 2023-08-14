from sc2.bot_ai import BotAI, Race
from sc2.data import Race, Difficulty
from sc2.player import Bot, Computer
from sc2.unit import Unit
from sc2.units import Units
from sc2.ids.unit_typeid import UnitTypeId
from sc2.constants import *
from sc2.ids.ability_id import AbilityId
from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.ids.buff_id import BuffId
import asyncio

class StalkerRushBot(BotAI):
  NAME: str = "StalkerRush"
  RACE: Race = Race.Protoss

  Iter5:int =0
  Iter20:int =0
  target_base_count:int = 3
  target_bg_count:int = 6
  
  buildingsCenter:Unit=None
  nexus2:Unit=None
  base2MainPylon:Unit=None

  def DoIter20(self):
    self.Iter20+=1
    # Make stalkers attack either closest enemy unit or enemy spawn location
    if self.units(UnitTypeId.STALKER).amount > 6:
      for stalker in self.units(UnitTypeId.STALKER).ready.idle:
          targets = (self.enemy_units | self.enemy_structures).filter(lambda unit: unit.can_be_attacked)
          if targets:
              target = targets.closest_to(stalker)
              stalker.attack(target)
          else:
              stalker.attack(self.enemy_start_locations[0])
    #print("Iter20 "+ str(self.Iter20))

  def DoIter5(self):
    self.Iter5+=1
    if(not self.nexus2 and self.structures(UnitTypeId.NEXUS).amount>=2):
      #nexus2 assign
      self.nexus2 = self.structures(UnitTypeId.NEXUS)[1]
    if(self.nexus2 and not self.base2MainPylon):
      nearNexus2Pylons = self.structures.ready(UnitTypeId.PYLON).filter( lambda p: p.position.distance_to(self.nexus2.position) <= 13)
      #for p in self.structures.ready(UnitTypeId.PYLON):
      if nearNexus2Pylons:
         self.base2MainPylon = nearNexus2Pylons.random
    pylonCount = self.structures(UnitTypeId.PYLON).amount
    #print("pylonCount "+str(pylonCount))
    if(pylonCount==0):
      self.buildingsCenter = self.townhalls.ready.random
    else:
      if(pylonCount<8 and self.base2MainPylon):
          self.buildingsCenter = self.base2MainPylon
      elif(pylonCount>4):
        self.buildingsCenter =self.structures.ready(UnitTypeId.PYLON).random
      elif(pylonCount>1):
        self.buildingsCenter = self.structures(UnitTypeId.PYLON)[1]
      else:
        self.buildingsCenter = self.structures(UnitTypeId.PYLON)[0]
        
    gasBuildings = self.structures.ready(UnitTypeId.ASSIMILATOR)
    if(gasBuildings):
        for gasBuilding in gasBuildings:
          gasDifference = 3-gasBuilding.assigned_harvesters
          if(gasDifference>0):
              workers = self.workers.filter(
                  lambda unit:  (unit.is_using_ability(AbilityId.HARVEST_RETURN) and unit.position.distance_to(gasBuilding.position) <= 8))
              if(workers):
                workers[0].gather(gasBuilding)
                workers[0].return_resource(None,False)
  
  def select_target(self):
    targets = self.enemy_structures
    if targets:
      return targets.random.position, True

    targets = self.enemy_units
    if targets:
      return targets.random.position, True

    if self.units and min([u.position.distance_to(self.enemy_start_locations[0]) for u in self.units]) < 5:
      return self.enemy_start_locations[0].position, False

    return self.mineral_field.random.position, False

  async def warp_new_units(self, proxy):
    mgRatio = float(self.minerals)/float(self.vespene+0.5)
    uid = UnitTypeId.STALKER
    if mgRatio>3 and self.vespene<200:
       uid = UnitTypeId.ZEALOT
    if mgRatio<0.4 and self.vespene>200:
       uid = UnitTypeId.SENTRY
    if self.can_afford(uid):
      for warpgate in self.structures(UnitTypeId.WARPGATE).ready:
        abilities = await self.get_available_abilities(warpgate)
        # all the units have the same cooldown anyway so let's just look at STALKER
        if AbilityId.WARPGATETRAIN_STALKER in abilities:
          pos = proxy.position.to2.random_on_distance(5)
          placement = await self.find_placement(AbilityId.WARPGATETRAIN_STALKER, pos, placement_step=1)
          if placement is None:
              # return ActionResult.CantFindPlacementLocation
              print("can't place")
              return
          warpgate.warp_in(uid, placement)

  async def on_start(self):
      print("Game started")
      print(self)
  async def on_end(self, result):
      print("Game ended.")
      print(str(result))
  async def on_step(self, iteration):
    #self.townhalls.random
    if not self.townhalls.ready:
          # Attack with all workers if we don't have any nexuses left, attack-move on enemy spawn (doesn't work on 4 player map) so that probes auto attack on the way
          for worker in self.workers:
              worker.attack(self.enemy_start_locations[0])
          return
    nexus = self.townhalls.ready.random

    if(iteration%20==0):
      self.DoIter20()
    if(iteration%5==0):
      self.DoIter5()

    if(iteration==0):
      await self.chat_send("(glhf)")
    
    # If this random nexus is not idle and has not chrono buff, chrono it with one of the nexuses we have
    if self.supply_workers + self.already_pending(UnitTypeId.PROBE) < self.townhalls.amount * 19:
      if not nexus.is_idle and not nexus.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
        nexuses = self.structures(UnitTypeId.NEXUS)
        abilities = await self.get_available_abilities(nexuses)
        for loop_nexus, abilities_nexus in zip(nexuses, abilities):
            if AbilityId.EFFECT_CHRONOBOOSTENERGYCOST in abilities_nexus:
                if loop_nexus.energy>75:
                  loop_nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nexus)
                  break
    
    # Distribute workers in gas and across bases
    await self.distribute_workers(1.6)

    # warp in stalkers
    if self.proxy_built and self.base2MainPylon:
      await self.warp_new_units(self.base2MainPylon)

    # build vr units
    if self.structures(UnitTypeId.ROBOTICSFACILITY):
      mgRatio = float(self.minerals)/float(self.vespene+0.5)
      for vr in self.structures(UnitTypeId.ROBOTICSFACILITY).ready.idle:
        if self.can_afford(UnitTypeId.IMMORTAL) and (mgRatio > 2 or self.minerals>350):
          vr.train(UnitTypeId.IMMORTAL)
        elif self.can_afford(UnitTypeId.OBSERVER) and (mgRatio < 0.35 or self.vespene>350):
          if(self.units(UnitTypeId.OBSERVER).amount + self.units(UnitTypeId.OBSERVERSIEGEMODE).amount)< 3: 
            vr.train(UnitTypeId.OBSERVER)

    # If we are low on supply, build pylon
    supplyUsed = self.supply_used
    pylonCount = self.structures(UnitTypeId.PYLON).amount
    if (
        pylonCount == 0
        or supplyUsed > 185 and self.supply_left < 6 and self.already_pending(UnitTypeId.PYLON) < 1
        or supplyUsed > 100 and self.supply_left < 11 and self.already_pending(UnitTypeId.PYLON) < 3
        or supplyUsed > 64 and self.supply_left < 8 and self.already_pending(UnitTypeId.PYLON) < 2
        or supplyUsed > 26 and self.supply_left < 5 and self.already_pending(UnitTypeId.PYLON) < 2
        or supplyUsed > 18 and self.supply_left < 4 and self.already_pending(UnitTypeId.PYLON) < 1
        or pylonCount < 2 and self.supply_left < 5 and self.already_pending(UnitTypeId.PYLON) < 1
    ):
        # Always check if you can afford something before you build it
        if self.can_afford(UnitTypeId.PYLON):
            print("build PYLON pylon/supplyUsed:"+str(pylonCount)+"/"+str(supplyUsed))
            print(self.main_base_ramp.protoss_wall_pylon)
            if pylonCount==0:
              await self.build(UnitTypeId.PYLON, self.main_base_ramp.protoss_wall_pylon, 3)
            elif pylonCount==1:
              if self.townhalls.ready.amount + self.already_pending(UnitTypeId.NEXUS) >=2:
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
              if(pylonCount>3 and pylonCount%2==0 and self.nexus2):
                await self.build(UnitTypeId.PYLON, self.nexus2, 18)
              else:
                await self.build(UnitTypeId.PYLON, self.buildingsCenter, int(supplyUsed) + 20)

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
            if self.can_afford(UnitTypeId.TWILIGHTCOUNCIL) and self.structures(UnitTypeId.TWILIGHTCOUNCIL).amount == 0 and self.already_pending(UnitTypeId.TWILIGHTCOUNCIL) == 0:
                await self.build(UnitTypeId.TWILIGHTCOUNCIL, near=self.buildingsCenter)
            elif self.structures.ready(UnitTypeId.TWILIGHTCOUNCIL) and self.can_afford(UnitTypeId.FORGE) and self.structures(UnitTypeId.FORGE).amount == 0 and self.already_pending(UnitTypeId.FORGE) == 0:
                await self.build(UnitTypeId.FORGE, near=self.buildingsCenter)
        else:
          # If we have no gateway, build gateway
          if self.can_afford(UnitTypeId.GATEWAY) and self.structures(UnitTypeId.GATEWAY).amount==0 and self.already_pending(UnitTypeId.GATEWAY) == 0:
              await self.build(UnitTypeId.GATEWAY, near=self.buildingsCenter)

    # build more BG
    if self.structures(UnitTypeId.PYLON).ready and self.structures(UnitTypeId.CYBERNETICSCORE).ready:
        bgCount = self.structures(UnitTypeId.GATEWAY).amount + self.already_pending(UnitTypeId.GATEWAY)+self.structures(UnitTypeId.WARPGATE).amount + self.already_pending(UnitTypeId.WARPGATE)
        
        if(bgCount>=3):
          if self.can_afford(UnitTypeId.ROBOTICSFACILITY) and self.structures(UnitTypeId.ROBOTICSFACILITY).amount==0 and self.already_pending(UnitTypeId.ROBOTICSFACILITY) == 0:
                await self.build(UnitTypeId.ROBOTICSFACILITY, near=self.buildingsCenter)

          # Research warp gate if cybercore is completed
          if (
              self.structures(UnitTypeId.CYBERNETICSCORE).ready and self.can_afford(AbilityId.RESEARCH_WARPGATE)
              and self.already_pending_upgrade(UpgradeId.WARPGATERESEARCH) == 0
          ):
            ccore = self.structures(UnitTypeId.CYBERNETICSCORE).ready.first
            ccore.research(UpgradeId.WARPGATERESEARCH)

        if (self.townhalls.ready.amount + self.already_pending(UnitTypeId.NEXUS) >= self.target_base_count):
          if (bgCount < self.target_bg_count):
            if self.can_afford(UnitTypeId.GATEWAY):
                print("build bg to max "+str(bgCount))
                #print(str(self.structures(UnitTypeId.GATEWAY).amount))
                #print(str(self.structures(UnitTypeId.WARPGATE).amount))
                #print(str(self.already_pending(UnitTypeId.GATEWAY)))
                #print(str(self.already_pending(UnitTypeId.WARPGATE)))
                await self.build(UnitTypeId.GATEWAY, near=self.buildingsCenter)
        else:
          if (bgCount < self.townhalls.ready.amount*2):
            if self.can_afford(UnitTypeId.GATEWAY):
                print("build bg to keep min "+str(bgCount))
                await self.build(UnitTypeId.GATEWAY, near=self.buildingsCenter)
    # Build gas near completed nexuses once we have a cybercore (does not need to be completed
    if self.structures(UnitTypeId.GATEWAY) and self.structures(UnitTypeId.ASSIMILATOR).amount==0 and self.already_pending(UnitTypeId.ASSIMILATOR)==0:
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