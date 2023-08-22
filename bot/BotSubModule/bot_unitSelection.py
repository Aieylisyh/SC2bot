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

class bot_unitSelection(BotAI):
    bot:StalkerRush.StalkerRushBot
    def __init__(self, bot:BotAI):
        self.bot=bot

    def all_amy(self):
        units= self.bot.units.filter(lambda p: not p.type_id==UnitTypeId.PROBE)
    def all_units(self):
        units= self.bot.units
    def all_attack_units(self):
        return self.bot.units.of_type(
            {UnitTypeId.PROBE,
            UnitTypeId.ADEPT, UnitTypeId.ZEALOT, UnitTypeId.SENTRY,  UnitTypeId.STALKER, 
            UnitTypeId.DARKTEMPLAR, UnitTypeId.ARCHON, UnitTypeId.HIGHTEMPLAR,
            UnitTypeId.COLOSSUS, UnitTypeId.DISRUPTOR,  UnitTypeId.IMMORTAL,
            UnitTypeId.PHOENIX, UnitTypeId.CARRIER, UnitTypeId.VOIDRAY, UnitTypeId.TEMPEST,
            UnitTypeId.MOTHERSHIP, UnitTypeId.MOTHERSHIPCORE}
        )
    def all_nonAttack_units(self):
        return self.bot.units.of_type(
            {UnitTypeId.OBSERVER, UnitTypeId.WARPPRISM}
        )
    
