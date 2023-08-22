
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
class bot_tactics(BotAI):
    bot:StalkerRush.StalkerRushBot
    def __init__(self, bot:BotAI):
        self.bot=bot
        
    #Our method to micro and to blink 
    async def micro(self):
        home_location = self.bot.start_location
        enemies: Units = self.bot.enemy_units | self.bot.enemy_structures
        enemies2 = self.bot.enemy_units.filter(lambda unit: unit.type_id not in {UnitTypeId.DRONE,UnitTypeId.SCV})
        enemies_can_attack: Units = enemies2.filter(lambda unit: unit.can_attack_ground)
        for stalker in self.bot.units(UnitTypeId.STALKER).ready:
            escape_location = stalker.position.towards(home_location, 6)
            enemyThreatsClose: Units = enemies_can_attack.filter(lambda unit: unit.distance_to(stalker) < 15)  # Threats that can attack the stalker
            if stalker.shield < 10 and enemyThreatsClose:
                abilities = await self.bot.get_available_abilities(stalker)
                if AbilityId.EFFECT_BLINK_STALKER in abilities:
                    #await self.bot.order(stalker, EFFECT_BLINK_STALKER, escape_location)
                    stalker(AbilityId.EFFECT_BLINK_STALKER, escape_location)
                    continue
                else: 
                    retreatPoints: Set[Point2] = self.bot.around8(stalker.position, distance=2) | self.bot.around8(stalker.position, distance=4)
                    # Filter points that are pathable
                    retreatPoints: Set[Point2] = {x for x in retreatPoints if self.bot.in_pathing_grid(x)}
                    if retreatPoints:
                        closestEnemy: Unit = enemyThreatsClose.closest_to(stalker)
                        retreatPoint: Unit = closestEnemy.position.furthest(retreatPoints)
                        stalker.move(retreatPoint)
                        continue  # Continue for loop, dont execute any of the following
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
        return {Point2((p.x - d, p.y)), Point2((p.x + d, p.y)), Point2((p.x, p.y - d)), Point2((p.x, p.y + d))}

    def GetAllCombatForces(self):
        units: Units = self.bot.units.of_type(
            {UnitTypeId.ZEALOT, UnitTypeId.SENTRY, UnitTypeId.OBSERVER, UnitTypeId.STALKER, UnitTypeId.IMMORTAL}
        )
        return units.ready.idle
