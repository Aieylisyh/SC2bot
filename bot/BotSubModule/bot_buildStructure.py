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

# import string

from bot.BotSubModule.botEnums.LocationPref import LocationPref


class bot_buildStructure:
    bot: BotAI

    def __init__(self, bot: BotAI):
        self.bot = bot

    target_BG_Count: int = 7

    supply_nexus = 15
    supply_pylon = 8

    nexus2: Unit = None
    base2MainPylon: Unit = None
    base1MainPylon: Unit = None

    base1CenterPylon: Unit = None

    def GetBuildingCount(
        self,
        id: UnitTypeId,
        ready: bool = True,
        building: bool = True,
        pending: bool = True,
    ):
        if id == UnitTypeId.NOTAUNIT:
            return 0

        b110 = self.bot.structures(id).amount
        b100 = self.bot.structures(id).ready.amount
        b011 = self.bot.already_pending(id)
        if ready and building and pending:
            return b100 + b011
        if ready and building and not pending:
            return b110
        if ready and not building and pending:
            return b100 * 2 + b011 - b110
        if ready and not building and not pending:
            return b100
        if not ready and building and pending:
            return b011
        if not ready and building and not pending:
            return b110 - b100
        if not ready and not building and pending:
            return b011 + b100 - b110
        if not ready and not building and not pending:
            return 0

    async def buildOne(
        self,
        id: UnitTypeId,
        minAmount: int,
        near: Unit | Point2,
        maxDistance=20,
        dependId: UnitTypeId = UnitTypeId.NOTAUNIT,
        dependProgress: float = 0,
        subId1: UnitTypeId = UnitTypeId.NOTAUNIT,
        subId2: UnitTypeId = UnitTypeId.NOTAUNIT,
        subId3: UnitTypeId = UnitTypeId.NOTAUNIT,
        subDependId1: UnitTypeId = UnitTypeId.NOTAUNIT,
        subDependId2: UnitTypeId = UnitTypeId.NOTAUNIT,
        subDependId3: UnitTypeId = UnitTypeId.NOTAUNIT,
    ):
        if not self.bot.can_afford(id):
            return

        amount = self.GetBuildingCount(id)
        amount += self.GetBuildingCount(subId1)
        amount += self.GetBuildingCount(subId2)
        amount += self.GetBuildingCount(subId3)

        if amount >= minAmount:
            return
        hasDepend = True
        if dependProgress > 0 and not dependId == UnitTypeId.NOTAUNIT:
            dependAmount = self.GetBuildingCount(dependId, True, True, False)
            dependAmount += self.GetBuildingCount(subDependId1, True, True, False)
            dependAmount += self.GetBuildingCount(subDependId2, True, True, False)
            dependAmount += self.GetBuildingCount(subDependId3, True, True, False)
            hasDepend = dependAmount >= dependProgress
        if hasDepend:
            await self.bot.build(id, near=near, max_distance=maxDistance)

    def GetSupplyCap(self, includingPending):
        if includingPending:
            return (
                self.GetBuildingCount(UnitTypeId.NEXUS) * self.supply_nexus
                + self.GetBuildingCount(UnitTypeId.PYLON) * self.supply_pylon
            )
        return self.bot.supply_cap

    @property
    def Ramp1PylonPos(self):
        return self.bot.main_base_ramp.protoss_wall_pylon

    @property
    def Pylon2Pos(self):
        # direction = nexus.position.negative_offset(self.buildingsCenter.position)
        return (
            self.bot.main_base_ramp.protoss_wall_pylon + self.bot.start_location
        ) * 0.5

    async def BuildPylons(self):
        bot = self.bot
        if not bot.can_afford(UnitTypeId.PYLON):
            return
        supplyUsed = bot.supply_used
        supplyExpected = self.GetSupplyCap(True)
        supplyLeft = supplyExpected - supplyUsed
        supplyLeft_real = (
            supplyLeft
            - self.GetBuildingCount(UnitTypeId.NEXUS, False, True, True)
            * self.supply_nexus
        )
        thisPylonNum = 1 + self.GetBuildingCount(UnitTypeId.PYLON)
        if (
            (
                supplyLeft_real < 3
                and self.GetBuildingCount(UnitTypeId.PYLON, False, True, True) == 0
            )
            or thisPylonNum == 1
            or supplyUsed > 185
            and supplyLeft < 7
            or supplyUsed > 100
            and supplyLeft < 10
            or supplyUsed > 64
            and supplyLeft < 8
            or supplyUsed > 30
            and supplyLeft < 6
            or supplyUsed > 18
            and supplyLeft < 4
        ):
            if thisPylonNum == 1:
                await self.buildOne(
                    UnitTypeId.PYLON, thisPylonNum, self.Ramp1PylonPos, 2
                )
            elif thisPylonNum == 2:
                await self.buildOne(
                    UnitTypeId.PYLON,
                    thisPylonNum,
                    self.Pylon2Pos,
                    3,
                    UnitTypeId.CYBERNETICSCORE,
                    0.3,
                )
            else:
                if thisPylonNum % 2 == 0:
                    await self.buildOne(
                        UnitTypeId.PYLON, thisPylonNum, self.base1CenterPylon, 20
                    )
                else:
                    await self.buildOne(
                        UnitTypeId.PYLON, thisPylonNum, self.bot.townhalls.random, 18
                    )

    # Build production buildings
    async def build_productions(self):
        bot = self.bot
        if not self.base1MainPylon and bot.structures(UnitTypeId.PYLON).ready:
            self.base1MainPylon = bot.structures(UnitTypeId.PYLON).closest_to(
                self.Ramp1PylonPos
            )
        if (
            self.base1MainPylon
            and not self.base1CenterPylon
            and bot.structures(UnitTypeId.PYLON).ready.amount == 2
        ):
            self.base1CenterPylon = bot.structures(UnitTypeId.PYLON).closest_to(
                self.Pylon2Pos
            )

        if not self.base1MainPylon:
            return

        buildCenter = self.base1MainPylon
        if self.base1CenterPylon:
            buildCenter = self.base1CenterPylon
        # BG 1
        await self.buildOne(
            UnitTypeId.GATEWAY,
            1,
            self.base1MainPylon,
            20,
            UnitTypeId.PYLON,
            1,
            subId1=UnitTypeId.WARPGATE,
        )
        # BY 1
        await self.buildOne(
            UnitTypeId.CYBERNETICSCORE,
            1,
            self.base1MainPylon,
            16,
            UnitTypeId.GATEWAY,
            1,
            subDependId1=UnitTypeId.WARPGATE,
        )
        # BG 2
        await self.buildOne(
            UnitTypeId.GATEWAY,
            2,
            self.base1MainPylon,
            16,
            UnitTypeId.GATEWAY,
            1,
            subId1=UnitTypeId.WARPGATE,
            subDependId1=UnitTypeId.WARPGATE,
        )
        # VC
        await self.buildOne(
            UnitTypeId.TWILIGHTCOUNCIL,
            1,
            buildCenter,
            20,
            UnitTypeId.NEXUS,
            1.1,
        )
        # BF
        await self.buildOne(
            UnitTypeId.FORGE,
            1,
            buildCenter,
            20,
            UnitTypeId.TWILIGHTCOUNCIL,
            0.3,
        )
        # BG 3~7
        if bot.supply_used > 99:
            await self.buildOne(
                UnitTypeId.GATEWAY,
                self.target_BG_Count,
                bot.structures(UnitTypeId.PYLON).ready.random,
                15,
                dependId=UnitTypeId.FORGE,
                dependProgress=1,
                subId1=UnitTypeId.WARPGATE,
            )
        elif bot.supply_used > 61:
            # VR
            await self.buildOne(
                UnitTypeId.ROBOTICSFACILITY,
                1,
                self.base1MainPylon,
                20,
                dependId=UnitTypeId.NEXUS,
                dependProgress=2,
            )
        elif bot.supply_used > 54:
            await self.buildOne(
                UnitTypeId.GATEWAY,
                3,
                bot.structures(UnitTypeId.PYLON).ready.random,
                15,
                dependId=UnitTypeId.FORGE,
                dependProgress=1,
                subId1=UnitTypeId.WARPGATE,
            )
