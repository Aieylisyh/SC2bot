import random
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
    attackForce_supply: int = 40

    def __init__(self, bot: BotAI):
        self.bot = bot
        self.unitSelection = bot.unitSelection
        self.tactics = bot.tactics

    async def Rush(self):
        bot = self.bot
        if bot.startingGame_stalkersRushed:
            return
        myForces = self.tactics.GetAllCombatForces()
        if myForces.amount >= 2:
            target = bot.enemy_start_locations[0].position
            bot.startingGame_stalkersRushed = True
            for f in myForces.idle:
                if f.can_attack:
                    f.attack(target)

    def AttackWithAllForces(self, includeWorkers: bool = True):
        bot = self.bot
        all_attack_units = self.unitSelection.all_units()
        if not includeWorkers:
            all_attack_units = self.unitSelection.all_amy()

        t = bot.enemy_start_locations[0]
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

    async def fight(self):
        bot = self.bot
        enemies = self.tactics.GetEnemies()
        enemy_fighters = self.tactics.GetEnemyAmy()
        if bot.supply_army > self.attackForce_supply:
            self.AttackWithAllForces(False)
            for stalker in bot.units(UnitTypeId.STALKER).ready.idle:
                if enemy_fighters:
                    # select enemies in range
                    in_range_enemies = enemy_fighters.in_attack_range_of(stalker)
                    if in_range_enemies:
                        # prioritize workers
                        workers = in_range_enemies(
                            {UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE}
                        )
                        if workers:
                            in_range_enemies = workers
                        # special micro for ranged units
                        if stalker.ground_range > 1:
                            # attack if weapon not on cooldown
                            if stalker.weapon_cooldown == 0:
                                # attack enemy with lowest hp of the ones in range
                                lowest_hp = min(
                                    in_range_enemies,
                                    key=lambda e: (e.health + e.shield, e.tag),
                                )
                                stalker.attack(lowest_hp)
                            else:
                                # micro away from closest unit
                                # move further away if too many enemies are near
                                friends_in_range = bot.units(
                                    UnitTypeId.STALKER
                                ).in_attack_range_of(stalker)
                                closest_enemy = in_range_enemies.closest_to(stalker)
                                distance = (
                                    stalker.ground_range
                                    + stalker.radius
                                    + closest_enemy.radius
                                )
                                if (
                                    len(friends_in_range) <= len(in_range_enemies)
                                    and closest_enemy.ground_range
                                    <= stalker.ground_range
                                ):
                                    distance += 1
                                else:
                                    # if more than 5 units friends are close, use distance one shorter than range
                                    # to let other friendly units get close enough as well and not block each other
                                    if (
                                        len(
                                            bot.units(UnitTypeId.STALKER).closer_than(
                                                7, stalker.position
                                            )
                                        )
                                        >= 5
                                    ):
                                        distance -= -1
                                stalker.move(
                                    closest_enemy.position.towards(stalker, distance)
                                )
                        else:
                            # target fire with melee units
                            lowest_hp = min(
                                in_range_enemies,
                                key=lambda e: (e.health + e.shield, e.tag),
                            )
                            stalker.attack(lowest_hp)
                    else:
                        # no unit in range, go to closest
                        stalker.move(enemy_fighters.closest_to(stalker))
                # no dangerous enemy at all, attack closest anything
                else:
                    stalker.attack(bot.enemy_start_locations[0])
        elif bot.units(UnitTypeId.STALKER).amount > 0:
            for stalker in bot.units(UnitTypeId.STALKER).ready.idle:
                if enemy_fighters:
                    # select enemies in range
                    in_range_enemies = enemy_fighters.in_attack_range_of(stalker)
                    if in_range_enemies:
                        # prioritize workers
                        workers = in_range_enemies(
                            {UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE}
                        )
                        if workers:
                            in_range_enemies = workers
                        # special micro for ranged units
                        if stalker.ground_range > 1:
                            # attack if weapon not on cooldown
                            if stalker.weapon_cooldown == 0:
                                # attack enemy with lowest hp of the ones in range
                                lowest_hp = min(
                                    in_range_enemies,
                                    key=lambda e: (e.health + e.shield, e.tag),
                                )
                                stalker.attack(lowest_hp)
                            else:
                                # micro away from closest unit
                                # move further away if too many enemies are near
                                friends_in_range = bot.units(
                                    UnitTypeId.STALKER
                                ).in_attack_range_of(stalker)
                                closest_enemy = in_range_enemies.closest_to(stalker)
                                distance = (
                                    stalker.ground_range
                                    + stalker.radius
                                    + closest_enemy.radius
                                )
                                if (
                                    len(friends_in_range) <= len(in_range_enemies)
                                    and closest_enemy.ground_range
                                    <= stalker.ground_range
                                ):
                                    distance += 1
                                else:
                                    # if more than 5 units friends are close, use distance one shorter than range
                                    # to let other friendly units get close enough as well and not block each other
                                    if (
                                        len(
                                            bot.units(UnitTypeId.STALKER).closer_than(
                                                7, stalker.position
                                            )
                                        )
                                        >= 5
                                    ):
                                        distance -= -1
                                stalker.move(
                                    closest_enemy.position.towards(stalker, distance)
                                )
                        else:
                            # target fire with melee units
                            lowest_hp = min(
                                in_range_enemies,
                                key=lambda e: (e.health + e.shield, e.tag),
                            )
                            stalker.attack(lowest_hp)
                    else:
                        # no unit in range, go to closest
                        stalker.move(enemy_fighters.closest_to(stalker))
                # no dangerous enemy at all, attack closest anything
        else:
            # our defense mechanic with our adepts
            for adept in bot.units(UnitTypeId.ADEPT).ready.idle:
                if enemy_fighters:
                    adept.attack(random.choice(enemy_fighters))
