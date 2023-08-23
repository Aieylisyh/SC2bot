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
from bot.BotSubModule.bot_unitSelection import bot_unitSelection
from bot.BotSubModule.bot_tactics import bot_tactics


class bot_mainStrategy:
    bot: BotAI
    unitSelection: bot_unitSelection
    tactics: bot_tactics
    attackForce_count: int = 16

    def __init__(self, bot: BotAI):
        self.bot = bot
        self.unitSelection = bot.unitSelection
        self.tactics = bot.tactics

    def AttackWithAllForces(self):
        bot = self.bot
        all_attack_units = bot_unitSelection.all_units(self)
        t = self.enemy_start_locations[0]
        for unit in all_attack_units:
            if unit.can_attack:
                unit.attack(t)

    def LaunchAttack(self):
        bot = self.bot
        if bot.already_pending_upgrade(UpgradeId.BLINKTECH) < 0.9:
            return

        myForces = self.tactics.GetAllCombatForces()
        if myForces.amount > self.attackForce_count:
            # targets = (self.enemy_units | self.enemy_structures).filter(lambda unit: unit.can_be_attacked)
            target = bot.enemy_start_locations[0].position
            for f in myForces.idle:
                if f.can_attack:
                    f.attack(target)
        return
