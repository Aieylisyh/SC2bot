from sc2.bot_ai import BotAI, Race
from sc2.data import Race, Difficulty
from sc2.player import Bot, Computer
from sc2.unit import Unit
from sc2.units import Units
from sc2.ids.unit_typeid import UnitTypeId
from sc2.constants import *
from sc2.ids.ability_id import AbilityId
import asyncio

class CarrierBot(BotAI):
  NAME: str = "CarrierBot"
  """This bot's name"""

  RACE: Race = Race.Protoss
  """This bot's Starcraft 2 race.
  
  Options are:
      Race.Terran
      Race.Zerg
      Race.Protoss
      Race.Random
  """
  Iter5:int =0
  Iter10:int =0
  Iter20:int =0

  def DoIter20(self):
    self.Iter20+=1
    print("Iter20 "+ str(self.Iter20))
  def DoIter10(self):
    self.Iter10+=1
  def DoIter5(self):
    self.Iter5+=1
  
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

  async def on_start(self):
      """
      This code runs once at the start of the game
      Do things here before the game starts
      """
      
      print("Game started")

  async def on_end(self):
      """
      This code runs once at the end of the game
      Do things here after the game ends
      """
      
      print("Game ended.")
      print(self)

  async def BuildMainBuildingOrder(self):
    nexus = self.townhalls[0]

    if(self.SimpleBuild(UnitTypeId.PYLON,nexus,5)):
      await asyncio.sleep(1)
    print("BuildMainBuildingOrder 1")
    if(self.SimpleBuild(UnitTypeId.GATEWAY,nexus,5)):
      await print("BuildMainBuildingOrder 3")
    if(self.BuildAssimilators(nexus)):
      await print("BuildMainBuildingOrder 4")
    if(self.SimpleBuild(UnitTypeId.CYBERNETICSCORE,nexus,5)):
      await print("BuildMainBuildingOrder 5")
    if(self.BuildAssimilators(nexus)):
      await print("BuildMainBuildingOrder 6")
    if(self.SimpleBuild(UnitTypeId.STARGATE,nexus,5)):
      await print("BuildMainBuildingOrder 7")
    if(self.SimpleBuild(UnitTypeId.FLEETBEACON,nexus,5)):
      await print("BuildMainBuildingOrder 8")
    

  def SimpleBuild(self, unitId:UnitTypeId, base:Unit, rangeNearBase:int = 5):
    if not self.structures(unitId) and self.already_pending(unitId) == 0 and self.can_afford(unitId):
      self.build(unitId, near= base.position.towards(self.game_info.map_center, rangeNearBase))
      return True
    return False

  def BuildAssimilators(self, base:Unit):
    if self.structures(UnitTypeId.PYLON).amount>=1 and self.structures(UnitTypeId.ASSIMILATOR).amount<2 and self.can_afford(UnitTypeId.ASSIMILATOR) and self.already_pending(UnitTypeId.ASSIMILATOR) == 0:
      vgs = self.vespene_geyser.closer_than(15, base)
      print("has vgs")
      print(vgs.amount)
      for vg in vgs:
        worker = self.select_build_worker(vg.position)
        if worker is None:
          break
        worker.build(UnitTypeId.ASSIMILATOR, vg, True)
        print("build ASSIMILATOR")
        print(worker.is_carrying_minerals())
        print(worker.is_gathering())
        worker.gather(self.mineral_field.closest_to(base), True)
        return True
    return False

  async def on_step(self, iteration):
    nexus = self.townhalls.ready.random
    #self.townhalls.random
    if not self.townhalls.ready:
          # Attack with all workers if we don't have any nexuses left, attack-move on enemy spawn (doesn't work on 4 player map) so that probes auto attack on the way
          for worker in self.workers:
              worker.attack(self.enemy_start_locations[0])
          return

    if(iteration%20==0):
      self.DoIter20()
    if(iteration%10==0):
      self.DoIter10()
    if(iteration%5==0):
      self.DoIter5()

    if(iteration==0):
      await self.BuildMainBuildingOrder()
      await self.chat_send("(glhf)")
    
    #print("RegularTickCheck")
    if self.supply_left < 8 and self.already_pending(UnitTypeId.PYLON) == 0 and self.can_afford(UnitTypeId.PYLON):
      await self.build(UnitTypeId.PYLON, near=nexus.position.towards(self.game_info.map_center, 5))

    # If this random nexus is not idle and has not chrono buff, chrono it with one of the nexuses we have
    if not nexus.is_idle and not nexus.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
        nexuses = self.structures(UnitTypeId.NEXUS)
        abilities = await self.get_available_abilities(nexuses)
        for loop_nexus, abilities_nexus in zip(nexuses, abilities):
            if AbilityId.EFFECT_CHRONOBOOSTENERGYCOST in abilities_nexus:
                loop_nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nexus)
                break
            
    self.RegularTickCheck()

  def RegularTickCheck(self):
    nexus = self.townhalls.random
          
    carriers = self.units(UnitTypeId.CARRIER)
    if carriers:
      target, target_is_enemy_unit = self.select_target()
      for carrier in carriers:
        if target_is_enemy_unit and (carrier.is_idle or carrier.is_moving):
          carrier.attack(target)
        elif carrier.is_idle:
          carrier.move(target)
    
    for worker in self.workers.idle:
      worker.gather(self.mineral_field.closest_to(nexus))

    for a in self.gas_buildings:
      if a.assigned_harvesters < a.ideal_harvesters:
        w = self.workers.closer_than(15, a)
        if w:
          chosenGasWorker=w.closest_to(a)
          chosenGasWorker.gather(a)
          chosenGasWorker.return_resource()
    
    if self.can_afford(UnitTypeId.CARRIER) and self.already_pending(UnitTypeId.CARRIER) < 1:
      stargate = self.structures(UnitTypeId.STARGATE).random
      stargate.train(UnitTypeId.CARRIER)