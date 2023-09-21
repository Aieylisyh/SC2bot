import random
from typing import Union
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
from bot.BotSubModule.bot_unitSelection import bot_unitSelection
import asyncio


class bot_tactics:
    bot: BotAI
    scoutTargetIndex: int
    ordered_expansions: None
    unitSelection: bot_unitSelection

    def __init__(self, bot: BotAI):
        self.bot = bot

    def Init(self):
        self.scouts_and_spots = {}
        self.scoutTargetIndex = 0
        self.ordered_expansions = None
        self.unitSelection = self.bot.mission.unitSelection

    # Cancel building on attack
    async def CancelAttackedBuildings(self):
        bot = self.bot
        for s in bot.structures.not_ready:
            if (
                s.build_progress < 1
                and s.build_progress > 0.15
                and s.shield_health_percentage < 0.25
            ):
                enes = self.unitSelection.GetInRangeUnits(
                    s, 8, self.unitSelection.GetUnits(True)
                )
                if enes and enes.amount > 1:
                    s(AbilityId.CANCEL)

    async def ScoutWithOb(self):
        # Method to send our obs scouting
        # We retrieve the list of possible extensions
        bot = self.bot
        # self.ordered_expansions = None
        if not self.ordered_expansions or len(self.ordered_expansions) == 0:
            self.ordered_expansions = sorted(
                # You are using 'self.expansion_locations', please use 'self.expansion_locations_list' (fast) or 'self.expansion_locations_dict' (slow) instead.
                bot.expansion_locations_list,
                key=lambda el: el.distance_to(bot.enemy_start_locations[0]),
                reverse=False,
            )
        # MORPH_OBSERVERMODE = 3739
        # MORPH_SURVEILLANCEMODE = 3741
        for obs in bot.units(UnitTypeId.OBSERVERSIEGEMODE).ready:
            detectors = self.unitSelection.GetInRangeEnemyDetectors(obs, obs)
            if detectors and detectors.amount > 0:
                obs(AbilityId.MORPH_OBSERVERMODE, queue=False)
                # direction = obs.position.offset(bot.start_location)
                direction = obs.position.negative_offset(
                    detectors.closest_n_units(obs, 1).first.position
                )
                obs.move(obs.position + direction.normalized * 8, queue=True)
                continue

            otherObs = self.unitSelection.GetInRangeAllyObservers(
                obs, obs.sight_range - 2
            )
            if otherObs and otherObs.amount > 0:
                obs(AbilityId.MORPH_OBSERVERMODE, queue=False)
                direction = obs.position.negative_offset(
                    otherObs.closest_n_units(obs, 1).first.position
                )
                obs.move(obs.position + direction.normalized * 6, queue=True)
                continue

            enes = self.unitSelection.GetInRangeUnits(
                obs, obs, self.unitSelection.GetUnits(True)
            )
            if not enes or enes.amount < 3:
                obs(AbilityId.MORPH_OBSERVERMODE, queue=False)

        for ob in bot.units(UnitTypeId.OBSERVER).ready:
            detectors = self.unitSelection.GetInRangeEnemyDetectors(ob, ob)
            if detectors and detectors.amount > 0:
                # direction = obs.position.offset(bot.start_location)
                direction = ob.position.negative_offset(
                    detectors.closest_n_units(ob, 1).first.position
                )
                ob.move(ob.position + direction.normalized * 8)
                continue
            enes = self.unitSelection.GetInRangeUnits(
                ob, ob, self.unitSelection.GetUnits(True)
            )
            otherObs = self.unitSelection.GetInRangeAllyObservers(
                ob, ob.sight_range, UnitTypeId.OBSERVERSIEGEMODE
            )
            otherOb = self.unitSelection.GetInRangeAllyObservers(
                ob, ob.sight_range, UnitTypeId.OBSERVER
            )
            if enes and enes.amount > 4 and not otherObs and not otherOb:
                ob(AbilityId.MORPH_SURVEILLANCEMODE, queue=False)
                continue

            if ob.is_idle:
                # scout
                maxIndex = 3
                if len(self.ordered_expansions) < 4:
                    maxIndex = 0
                elif len(self.ordered_expansions) < 6:
                    maxIndex = 1
                elif len(self.ordered_expansions) < 8:
                    maxIndex = 2
                targetLocation = self.ordered_expansions[self.scoutTargetIndex]
                self.scoutTargetIndex += 1
                if self.scoutTargetIndex > maxIndex:
                    self.scoutTargetIndex = 0
                ob.move(targetLocation)

    async def OracleRush(self):
        bot = self.bot
        oracles = bot.units(UnitTypeId.ORACLE).ready
        if not oracles or oracles.amount < 1:
            return
        for oracle in oracles:
            m = getattr(oracle, "mission", None)
            print(oracle.tag)
            print(m)
            # oracle.tag+=1 read only
            # don't know why the mission attri is missing every iteration
            if m is not None:
                continue

            enemiesUnits = self.unitSelection.GetUnits(True)
            eneBuilding = bot.enemy_structures
            enemies: Units = enemiesUnits + eneBuilding
            eneTargets: Unit = self.unitSelection.GetUnits(True)
            # good target:worker marine
            # practise, download some to study
            # TODO attack workers, move between ene bases, open weapon when more than 2 works in range and enemy>50
            # close weapon if no works in range of 10 and energy>4
            print("assign missions")
            ms = bot_mission(bot)
            ms.id = "oracle_harass"
            await bot.chat_send("oracle harass")
            # oracle.mission = ms
            setattr(oracle, "mission", ms)
            print(oracle.mission.id)
            m = getattr(oracle, "mission", None)
            print(m)
            enemyThreatsClose: Units = enemiesUnits.filter(
                lambda unit: unit.distance_to(oracle) > 8
                and unit.distance_to(oracle) <= 12
            )

    # Our method to micro and to blink
    async def StalkerEscape(
        self, stalker: Unit, home_location: Point2, enemies_can_attack: Units
    ):
        bot = self.bot
        escape_location = stalker.position.towards(home_location, 5)
        # Threats that can attack the stalker
        enemyThreatsClose1: Units = enemies_can_attack.filter(
            lambda unit: unit.distance_to(stalker) > 8
            and unit.distance_to(stalker) <= 12
        )
        enemyThreatsClose2: Units = enemies_can_attack.filter(
            lambda unit: unit.distance_to(stalker) > 6
            and unit.distance_to(stalker) <= 8
        )
        enemyThreatsClose3: Units = enemies_can_attack.filter(
            lambda unit: unit.distance_to(stalker) <= 6
        )
        enemyThreatsClose: Units = enemies_can_attack.filter(
            lambda unit: unit.distance_to(stalker) <= 12
        )
        threatRating = 0
        for e in enemyThreatsClose1:
            threatRating += bot.calculate_supply_cost(e.type_id) * 1
        for e in enemyThreatsClose2:
            threatRating += bot.calculate_supply_cost(e.type_id) * 2
        for e in enemyThreatsClose3:
            threatRating += bot.calculate_supply_cost(e.type_id) * 3
        shouldRetreat = (threatRating > 12 and stalker.shield_percentage < 0.5) or (
            threatRating > 8 and stalker.shield_percentage < 0.1
        )
        if shouldRetreat:
            abilities = await self.bot.get_available_abilities(stalker)
            if AbilityId.EFFECT_BLINK_STALKER in abilities:
                # await self.bot.order(stalker, EFFECT_BLINK_STALKER, escape_location)
                stalker(AbilityId.EFFECT_BLINK_STALKER, escape_location)
                return
            else:
                if stalker.shield == 0:
                    await self.Retreat(stalker, home_location)
                    return
                distanceRetreat = 2
                retreatPoints: Set[Point2] = self.unitSelection.around8(
                    stalker.position, distance=distanceRetreat
                ) | self.unitSelection.around8(
                    stalker.position, distance=distanceRetreat * 2
                )
                # Filter points that are pathable
                retreatPoints: Set[Point2] = {
                    x for x in retreatPoints if self.bot.in_pathing_grid(x)
                }
                if retreatPoints:
                    closestEnemy: Unit = enemyThreatsClose.closest_to(stalker)
                    retreatPoint: Unit = closestEnemy.position.furthest(retreatPoints)
                    stalker.move(retreatPoint)

    async def MoveUnitsTogether(self, u: Unit, home_location: Point2):
        allies = self.unitSelection.GetUnits(False)
        nearby = self.unitSelection.UnitsInRangeOfUnit(u, allies, 6.5)
        if not nearby:
            return

        if nearby and nearby.amount > 2:
            p = nearby.center
            u.move(p)
            return

    async def MicroMoveUnit(
        self, u: Unit, home_location: Point2, enemies_can_attack: Units
    ):
        # TODO chase weak target enemies or hide from enemies
        # only move, no attack
        bot = self.bot
        enemiesUnits = self.unitSelection.GetUnits(True, workers=True)
        enemies = enemiesUnits + bot.enemy_structures
        # python  append没有返回值 可以用 加号
        if not enemiesUnits:
            if enemies.amount > 0:
                u.move(u.position.towards(enemies.center))
            return
        nearestEne: Unit = enemiesUnits.closest_to(u)
        isMelee = False
        if u._weapons:
            if u._weapons[0].range <= 3.25:
                isMelee = True

        lowHpFactor = 0
        if u.shield_health_percentage < 0.5:
            lowHpFactor = 100
        elif u.shield_health_percentage < 0.3:
            lowHpFactor = 250

        allies = self.unitSelection.GetUnits(False)
        allies = self.unitSelection.FilterAttack(allies)
        allies = allies.ready.filter(lambda unit: not unit == u)
        allyForce = self.GetNearbyForceEstimate(u, allies)
        eneForce = self.GetNearbyForceEstimate(u, enemies)
        weAreStronger = allyForce > eneForce * 1.6 + lowHpFactor
        if u.is_flying:
            weAreStronger = False
        weAreWeaker = allyForce < eneForce * 1 + lowHpFactor
        if isMelee and not weAreWeaker:
            weAreStronger = True
        # print(   "weAreStronger " + str(weAreStronger) + " weAreWeaker " + str(weAreWeaker) )
        if weAreStronger:
            u.move(u.position.towards(nearestEne.position))
            return

        if u.type_id == UnitTypeId.STALKER and (random.random() > 0.5 or weAreWeaker):
            await self.StalkerEscape(u, home_location, enemies_can_attack)
            return
        if weAreWeaker:
            await self.Retreat(u, home_location)
            return

        await self.MoveToTacticPos(u, home_location)

    async def MoveToTacticPos(self, u: Unit, home_location: Point2):
        r = random.random() > 0.35
        if r:
            u.move(home_location)
        else:
            await self.MoveUnitsTogether(u, home_location)

    def GetNearbyForceEstimate(self, u: Unit, allies: Units):
        res = 0
        nearby0 = self.unitSelection.UnitsInRangeOfUnit(u, allies, 5)
        for a in nearby0:
            res += self.unitSelection.GetUnitPowerValue(a)
        nearby1 = self.unitSelection.UnitsInRangeOfUnit(u, allies, 8)
        for a in nearby1:
            res += self.unitSelection.GetUnitPowerValue(a) * 0.5
        nearby2 = self.unitSelection.UnitsInRangeOfUnit(u, allies, 14)
        for a in nearby2:
            res += self.unitSelection.GetUnitPowerValue(a) * 0.25
        return res

    async def UnitAbilityActive(self, u: Unit, enes: Units):
        if u.type_id == UnitTypeId.SENTRY:
            abilities = await self.bot.get_available_abilities(u)
            if AbilityId.GUARDIANSHIELD_GUARDIANSHIELD in abilities:
                allies = self.unitSelection.GetUnits(False, True, False)
                allies = self.unitSelection.UnitsInRangeOfUnit(u, allies, 5)
                if allies.amount <= 2:
                    return

                enes = self.unitSelection.UnitsInRangeOfUnit(u, enes, 10)
                enes = self.unitSelection.FilterAttack(enes)
                rangedEneAmount = 0
                for e in enes:
                    if (
                        e.can_attack_ground
                        and len(e._weapons) > 0
                        and e._weapons[0]
                        and e._weapons[0].range > 3
                    ):
                        rangedEneAmount += 1
                if rangedEneAmount > 3:
                    u(AbilityId.GUARDIANSHIELD_GUARDIANSHIELD)
        if u.type_id == UnitTypeId.VOIDRAY:
            abilities = await self.bot.get_available_abilities(u)
            if AbilityId.EFFECT_VOIDRAYPRISMATICALIGNMENT in abilities:
                enes = self.unitSelection.UnitsInRangeOfUnit(u, enes, 6.5)
                if enes:
                    armoredCount = 0
                    for e in enes:
                        if e.is_armored:
                            armoredCount += 1
                    if armoredCount * 2 >= enes.amount:
                        u(AbilityId.EFFECT_VOIDRAYPRISMATICALIGNMENT)

    async def Retreat(self, u: Unit, safePos):
        if not safePos:
            safePos = self.bot.start_location
        u.move(safePos)

    async def Micro(self):
        bot = self.bot
        enemiesUnits = self.unitSelection.GetUnits(True, workers=True)
        eneBuilding = bot.enemy_structures
        enemies: Units = enemiesUnits + eneBuilding
        home_location = self.bot.start_location
        if not enemies:
            return
        allUnits = self.unitSelection.GetUnits(False).ready
        for u in allUnits:
            # print(u)
            await self.UnitAbilityActive(u, enemies)

            info = self.GetGoodAttackInfo(u, 0.05, 5)
            if info[0]:
                await u.attack(info[1])
                continue
            await self.MicroMoveUnit(u, home_location, enemies)
            continue

    # attack only when this attack is very high cost efficiency
    # no wait, high damage bonus, one shot, etc
    def GetGoodAttackInfo(
        self,
        u: Unit,
        cdThreshold: float = 0.5,
        allowShots: int = 4,
        onlyShots: int = -1,
    ) -> tuple[bool, Unit, float]:
        if not u.can_attack:
            return tuple(False, None, 0)
        if u.weapon_cooldown < 0:
            return tuple(False, None, 0)
        bot = self.bot
        if u.weapon_cooldown > cdThreshold:
            return tuple(False, None, 0)

        enemiesUnits = self.unitSelection.GetUnits(True, workers=True)
        if not enemiesUnits:
            return tuple(False, None, 0)
        eneBuilding = bot.enemy_structures
        enemies: Units = enemiesUnits + eneBuilding
        if not enemies:
            return tuple(False, None, 0)

        groundEnes = enemies.filter(lambda u: u.is_structure or (not u.is_flying))
        airEnes = enemies.filter(lambda u: u.is_flying)

        attackableEnes: Units = Units(None, bot)
        distCanGo = u.weapon_cooldown * u.movement_speed
        if u.real_speed < u.movement_speed:
            distCanGo * 0.6

        if u.can_attack_ground:
            attackableEnes.append(
                self.unitSelection.UnitsInRangeOfUnit(
                    u, groundEnes, u.ground_range + distCanGo
                )
            )
        if u.can_attack_air:
            attackableEnes.append(
                self.unitSelection.UnitsInRangeOfUnit(
                    u, airEnes, u.air_range + distCanGo
                )
            )

        if not attackableEnes:
            return tuple(False, None, 0)

        for e in attackableEnes:
            dmg = u.calculate_damage_vs_target(e)
            # u.calculate_damage_vs_target
            # Returns a tuple of: [potential damage against target, attack speed, attack range] : Tuple[float, float, float]:
            dmgValue = dmg[0]
            eneHp = e.health + e.shield
            shots = 10
            # print(e)
            if dmgValue > 0:
                shots = float(eneHp) / dmgValue
                if onlyShots > 0 and shots > onlyShots:
                    return tuple(False, None, 0)
            oneShotBonus = 0
            if shots <= 1:
                oneShotBonus = 60
            elif allowShots >= 2 and shots <= 2:
                oneShotBonus = 32
            elif allowShots >= 3 and shots <= 3:
                oneShotBonus = 16
            elif allowShots >= 4 and shots <= 4:
                oneShotBonus = 8
            elif allowShots >= 5 and shots <= 5:
                oneShotBonus = 3
            dmg = u.calculate_damage_vs_target(e)[0]
            e.tpv = (
                dmg
                + oneShotBonus
                + self.unitSelection.DamageDealBonusToAjustAttackPriority(e)
                - u.weapon_cooldown * dmg * 0.6
            )

        eneToAttackSortedList = sorted(
            attackableEnes,
            key=lambda e: e.tpv,
            reverse=True,
        )
        # print(eneToAttackSortedList)
        # print("target " + str(eneToAttackSortedList[0]))
        bestToAttackUnit = eneToAttackSortedList[0]
        return tuple(True, bestToAttackUnit, bestToAttackUnit.tpv)
