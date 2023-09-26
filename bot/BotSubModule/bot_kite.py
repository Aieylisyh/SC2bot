import math
import random
from typing import Union
from sc2.bot_ai import BotAI, Race
from sc2.data import Race, Difficulty
from sc2.player import Bot, Computer
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from sc2.units import Units
from sc2.ids.unit_typeid import UnitTypeId
from sc2.constants import *
from sc2.ids.ability_id import AbilityId
from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.ids.buff_id import BuffId
from bot.BotSubModule.bot_unitSelection import bot_unitSelection
from bot.BotSubModule.bot_tactics import bot_tactics


class bot_kite:
    bot: BotAI
    unitSelection: bot_unitSelection
    tactics: bot_tactics

    timeStep: float
    timeStepIgnore: float

    def __init__(self, bot: BotAI, t: bot_tactics):
        self.bot = bot
        self.unitSelection = self.bot.unitSelection
        self.tactics = t

        self.timeStep = 0.5
        self.timeStepIgnore = 0.2

    def GetTimeStep(self, totalTime: float):
        if totalTime <= 0:
            return self.timeStepIgnore
        if totalTime < self.timeStep + self.timeStepIgnore:
            return totalTime
        return self.timeStep

    def Calculate_Pos_Score(
        self,
        p: Point2,
        futurePosition: Point2,
        factor_threat: float = 1,
        factor_reward: float = 1,
        factor_future: float = 1,
    ) -> int:
        score_threat = self.Calculate_Pos_Threat(p)
        score_reward = self.Calculate_Pos_Reward(p)
        score_future = self.Calculate_Pos_FutureBenefit(p, futurePosition)
        return (
            score_threat * factor_threat
            + score_reward * factor_reward
            + score_future * factor_future
        )

    def Calculate_Pos_Threat(self, p: Point2) -> int:
        v: int = 0

        return v

    def Calculate_Pos_Reward(self, p: Point2) -> int:
        v: int = 0

        return v

    def Calculate_Pos_FutureBenefit(self, p: Point2, futurePosition: Point2) -> int:
        v: int = 0

        return v

    def Calculate_EneReward(e: Unit):
        # base on supply, mineral gas cost, build time, tech height, energy left, passagers inside
        v = 0

        print(v)

    def GetKiteThinkRange(self):
        bot = self.bot
        # bot.step_time
        # the range arround the unit to take into consideration,
        # in early game it can be 10 since there is no long range attackers,
        # in mid game vs Terran, tank must be taken into consider so it can be 15, other wise 12 is enough
        # in late game it can be 15

        hasMidRangeEnemies = False
        hasLongRangeEnemies = False
        eneLong = bot.enemy_units.filter(
            lambda unit: unit.type_id
            in {
                UnitTypeId.COLOSSUS,
                UnitTypeId.SIEGETANK,
                UnitTypeId.TEMPEST,
                UnitTypeId.BROODLORD,
            }
        )

        if eneLong.ready.amount > 0:
            return 15

        if bot.time < 270:
            return 10
        elif bot.time < 500:
            if bot.enemy_race == Race.Terran:
                return 15
            return 12
        else:
            return 15

    async def KiteGroup(
        self,
        u: Unit,
        futurePosition: Point2,
        aggressiveFactor: float = 1,
        sneakyFactor: float = 0,
        group: Units = None,
        # TODO
        # a group of unit that follow's their leader,
        # #but only the leader need costy algorithm,
        # the group is often in 2 3 or 4 units, if small unit like zergling may have 5 or 6 at max
        groupDistance: float = 0.8,
        # TODO
        # swarm the unit's group, the group should not distance for more than this distance
    ):
        bot = self.bot
        self.Kite(u, futurePosition, aggressiveFactor, sneakyFactor)

    def GetDirByRadianDelta(self, u: Unit, radian: float) -> Point2:
        rad = u.facing + radian
        dir = Point2((math.cos(rad), math.sin(rad)))
        return dir

    def GetPosByRadianDelta(self, u: Unit, time: float, radian: float) -> Point2:
        t = self.tactics.GetTurnTime(radian)
        goTime = time - t
        if goTime <= 0:
            return u.position
        speed = u.real_speed
        return self.GetDirByRadianDelta(u, radian) * speed * 1.4 * goTime + u.position

    async def Kite_offensive(self, u: Unit, futurePosition: Point2):
        await self.Kite(u, futurePosition, 0.25, 0.75, 0.75)

    async def Kite_normal(self, u: Unit, futurePosition: Point2):
        await self.Kite(u, futurePosition, 0.5, 1, 0.25)

    async def Kite_defensive(self, u: Unit, futurePosition: Point2):
        await self.Kite(u, futurePosition, 0.75, 0.5, 1)

    async def Kite_retreat(self, u: Unit, futurePosition: Point2):
        await self.Kite(u, futurePosition, 1, 0.25, 0.75)

    # complex algorithm to be used for all combat units moves
    async def Kite(
        self,
        u: Unit,
        futurePosition: Point2,  # often enemy base for offensive mode and our base for defensive mode
        factor_threat: float = 1,
        factor_reward: float = 1,
        factor_future: float = 1,
        sneakyFactor: float = 0,  # TODO hide from enaging the enemies, good to use for DarkTemplars
    ):
        wcd = u.weapon_cooldown
        if wcd < 0:
            return

        if wcd == 0:
            info = self.tactics.GetGoodAttackInfo(u, 0)
            if info[0]:
                await u.attack(info[1])
                return

        bot = self.bot
        thinkRange = self.GetKiteThinkRange()
        timeStep = self.GetTimeStep(wcd)
        # iter1 origin, 0, 0.5pi, 1pi, 1.5pi, 2pi
        # iter2 0.25pi, 0.75pi, 1.25pi, 1.75pi,
        # iter3 1/8pi, 3/8pi, 5/8pi, 7/8pi, 9/8pi, 11/8pi, 13/8pi, 15/8pi

        calculatedPoints: list[tuple[float, Point2, int]] = []  # pos, score
        calculatedPoints += (
            -1,  # origin
            u.position,
            self.Calculate_Pos_Score(
                u.position, futurePosition, factor_threat, factor_reward, factor_future
            ),
        )

        # iter1
        pendingPoints: list[tuple[float, Point2, int]] = []
        print("iter1 ", timeStep)
        print("pos ", u.position)
        for i in range(4):  # 0123
            rad = math.pi * i * 0.5
            iPos = self.GetPosByRadianDelta(u, timeStep, rad)

            iScore = self.Calculate_Pos_Score(
                iPos, futurePosition, factor_threat, factor_reward, factor_future
            )
            p = (rad, iPos, iScore)
            calculatedPoints += p  # same as append
            print("rad ", round(rad, 2), " pos ", iPos, " score ", iScore)
            pp = (rad, iPos, iScore)
            pendingPoints.append(pp)  # same as +=

        goodPendingPoints = bot_kite.FilterGoodPoints(pendingPoints)

    def FilterGoodPoints(
        given: list[tuple[float, Point2, int]]
    ) -> list[tuple[float, Point2, int]]:
        res: list[tuple[float, Point2, int]] = []
        average: float = 0.0
        for g in given:
            average += g[2]
        average = average / len(given)
        for g in given:
            if g[2] >= average:
                res += g
        return res
