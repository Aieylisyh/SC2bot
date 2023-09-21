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
from bot.BotSubModule.bot_buildStructure import bot_buildStructure


class bot_economy:
    bot: BotAI

    def __init__(self, bot: BotAI):
        self.bot = bot
        self.buildStructure = (
            bot.buildStructure
        )  # here need to use dynamic var buildStructure to assign into self.buildStructure, to avoid circular import

    buildStructure: bot_buildStructure

    supply_nexus = 15
    supply_pylon = 8
    mineralFieldCount = 8
    vespineGasCount = 2

    target_Base_Count: int = 3

    @property
    def workerCapPerTownhall(self):
        return self.mineralFieldCount * 2 + self.vespineGasCount * 3

    def GetSupplyCap(self, includePending):
        if includePending:
            return (
                self.buildStructure.GetBuildingCount(UnitTypeId.NEXUS)
                * self.supply_nexus
                + self.buildStructure.GetBuildingCount(UnitTypeId.PYLON)
                * self.supply_pylon
            )
        return self.bot.supply_cap

    async def TrainWorkers(self):
        if not self.bot.can_afford(UnitTypeId.PROBE):
            return
        # print("TrainWorkers1")
        townhalls = self.bot.townhalls
        targetWorker = min(
            townhalls.amount * self.workerCapPerTownhall, self.GetSupplyCap(True)
        )
        for townhall in townhalls:
            if (
                townhall.is_idle
                and townhall.is_ready
                and self.bot.supply_workers + self.bot.already_pending(UnitTypeId.PROBE)
                < targetWorker
            ):
                townhall.train(UnitTypeId.PROBE)
                # print("TrainWorkers2")

    # Build gas assimilators
    async def BuildAssimilators(self):
        bot = self.bot
        # assimilatorCount = self.bot.buildStructure.GetBuildingCount(UnitTypeId.ASSIMILATOR)
        townhalls = bot.townhalls.ready
        probeCount = bot.units(UnitTypeId.PROBE).amount + bot.already_pending(
            UnitTypeId.PROBE
        )
        n = townhalls.amount * self.mineralFieldCount * 2
        # print("BuildAssimilators")
        # print(probeCount)
        # print(n)
        if probeCount >= n + 1 and bot.structures(UnitTypeId.GATEWAY).amount > 0.5:
            # build 1 assimilator
            await self.BuildAssimilator(townhalls, 1)
        if (
            probeCount >= n + 3
            and bot.structures(UnitTypeId.NEXUS).amount > 1
            and bot.startingGame_rusherRushed
        ):
            # build 1 assimilator
            await self.BuildAssimilator(townhalls, 2)

    async def BuildAssimilator(self, townhalls: Units, amount: int):
        if not self.bot.can_afford(UnitTypeId.ASSIMILATOR):
            return
        if self.bot.already_pending(UnitTypeId.ASSIMILATOR):
            return
        for townhall in townhalls:
            vgs = self.bot.vespene_geyser.closer_than(15, townhall)
            assimilatorAmount = (
                self.bot.structures(UnitTypeId.ASSIMILATOR)
                .closer_than(15, townhall)
                .amount
            )
            # print("assimilatorAmount should less than")
            # print(assimilatorAmount)
            # print(amount)
            if assimilatorAmount >= amount:
                break
            for vg in vgs:
                assimilatorCount = self.bot.gas_buildings.closer_than(1, vg).amount
                if assimilatorCount >= 1:
                    continue
                worker = self.bot.select_build_worker(vg.position)
                if worker is None:
                    break
                # print("BuildAssimilator")
                # print(amount)
                worker.build(UnitTypeId.ASSIMILATOR, vg)
                worker.stop(queue=True)

    async def StartGameAllocateWorkers(self):
        bot = self.bot
        workerPool = bot.workers.filter(
            lambda unit: (
                unit.is_using_ability(AbilityId.HARVEST_GATHER) | unit.is_idle
            )
        )
        base = bot.townhalls.ready[0]
        # local_minerals_tags = {mineral.tag for mineral in bot.mineral_field if mineral.distance_to(base) <= 8}
        local_minerals = {
            mineral for mineral in bot.mineral_field if mineral.distance_to(base) <= 12
        }
        for m in local_minerals:
            if len(workerPool) < 1:
                break
            w = workerPool.closest_to(m)
            workerPool.remove(w)
            w.gather(m)
        length = workerPool.amount
        restMinerals = bot.mineral_field.closest_n_units(base, length)
        for m in restMinerals:
            w = workerPool.closest_to(m)
            workerPool.remove(w)
            w.gather(m)

    async def AllocateAllWorkers(self):
        bot = self.bot
        if not bot.mineral_field or not bot.workers or not bot.townhalls.ready:
            return

        # globalWorkerPool=bot.workers.filter( lambda unit: (unit.is_using_ability(AbilityId.HARVEST_GATHER)|unit.is_idle))
        bases = bot.townhalls.ready
        for base in bases:
            difference = base.surplus_harvesters
            if difference > 0:
                # this base has more than idea workers
                # needs to spare difference workers out
                print(difference)
            local_minerals_tags = {
                mineral.tag
                for mineral in bot.mineral_field
                if mineral.distance_to(base) <= 8
            }
            local_workers = bot.workers.filter(
                lambda unit: unit.order_target in local_minerals_tags
                or (unit.is_carrying_minerals and unit.order_target == base.tag)
            )

    async def DistributeWorkers(self):
        bot = self.bot
        if not bot.mineral_field or not bot.workers or not bot.townhalls.ready:
            return

        resource_ratio = 1
        if bot.supply_used < 20:
            resource_ratio = 6
        elif bot.supply_used < 35:
            resource_ratio = 2.7
        elif bot.supply_used < 50:
            resource_ratio = 2.4
        elif bot.supply_used < 80:
            resource_ratio = 1.8
        elif bot.supply_used < 120:
            resource_ratio = 1.6
        elif bot.supply_used < 160:
            resource_ratio = 1.3
        worker_pool = bot.workers.idle
        # print("worker_pool.amount")
        # print(worker_pool.amount)
        # add more not idle ming work
        # worker_pool.append(self.workers.filter(
        #            lambda unit:  (unit.is_using_ability(AbilityId.HARVEST_RETURN) )))

        gas_buildings = bot.gas_buildings.ready

        # list of places that need more workers
        deficit_mining_places = []
        bases = bot.townhalls.ready
        for mining_place in bases | gas_buildings:
            difference = mining_place.surplus_harvesters
            # print(mining_place)
            # print(difference)#-4
            # print(mining_place.ideal_harvesters)#16
            # print(mining_place.assigned_harvesters)#16
            # perfect amount of workers, skip mining place
            if not difference:
                continue
            if mining_place.has_vespene:
                # get all workers that target the gas extraction site
                # or are on their way back from it
                local_workers = bot.workers.filter(
                    lambda unit: unit.order_target == mining_place.tag
                    or (
                        unit.is_carrying_vespene
                        and unit.order_target == bases.closest_to(mining_place).tag
                    )
                )
            else:
                # get tags of minerals around expansion
                local_minerals_tags = {
                    mineral.tag
                    for mineral in bot.mineral_field
                    if mineral.distance_to(mining_place) <= 8
                }
                # get all target tags a worker can have
                # tags of the minerals he could mine at that base
                # get workers that work at that gather site
                local_workers = bot.workers.filter(
                    lambda unit: unit.order_target in local_minerals_tags
                    or (
                        unit.is_carrying_minerals
                        and unit.order_target == mining_place.tag
                    )
                )
            # too many workers
            if difference > 0:
                for worker in local_workers[:difference]:
                    worker_pool.append(worker)
            # too few workers
            # add mining place to deficit bases for every missing worker
            else:
                deficit_mining_places += [mining_place for _ in range(-difference)]

        # prepare all minerals near a base if we have too many workers
        # and need to send them to the closest patch

        # print("worker_pool "+str(len(worker_pool)))
        # print("deficit_mining_places "+str(len(deficit_mining_places)))
        if len(worker_pool) > len(deficit_mining_places):
            all_minerals_near_base = [
                mineral
                for mineral in bot.mineral_field
                if any(mineral.distance_to(base) <= 8 for base in bot.townhalls.ready)
            ]
        # distribute every worker in the pool
        for worker in worker_pool:
            # as long as have workers and mining places
            # print("worker")
            # print(worker)
            if deficit_mining_places:
                # choose only mineral fields first if current mineral to gas ratio is less than target ratio
                if (
                    bot.vespene
                    and bot.minerals / bot.vespene < resource_ratio
                    and bot.vespene > 100
                ):
                    possible_mining_places = [
                        place
                        for place in deficit_mining_places
                        if not place.vespene_contents
                    ]
                # else prefer gas
                else:
                    possible_mining_places = [
                        place
                        for place in deficit_mining_places
                        if place.vespene_contents
                    ]
                # if preferred type is not available any more, get all other places
                if not possible_mining_places:
                    possible_mining_places = deficit_mining_places
                # find closest mining place
                current_place = min(
                    deficit_mining_places, key=lambda place: place.distance_to(worker)
                )
                # remove it from the list
                deficit_mining_places.remove(current_place)
                # if current place is a gas extraction site, go there
                if current_place.vespene_contents:
                    worker.gather(current_place)
                    worker.return_resource(None, False)
                # if current place is a gas extraction site,
                # go to the mineral field that is near and has the most minerals left
                else:
                    local_minerals = (
                        mineral
                        for mineral in bot.mineral_field
                        if mineral.distance_to(current_place) <= 8
                    )
                    # local_minerals can be empty if townhall is misplaced
                    target_mineral = max(
                        local_minerals,
                        key=lambda mineral: mineral.mineral_contents,
                        default=None,
                    )
                    if target_mineral:
                        worker.gather(target_mineral)
                        worker.return_resource(None, False)
            # more workers to distribute than free mining spots
            # send to closest if worker is doing nothing
            elif worker.is_idle and all_minerals_near_base:
                target_mineral = min(
                    all_minerals_near_base,
                    key=lambda mineral: mineral.distance_to(worker),
                )
                worker.gather(target_mineral)
            else:
                # there are no deficit mining places and worker is not idle
                # so dont move him
                pass

    async def Expand(self):
        # expand base
        bot = self.bot
        baseCount = self.buildStructure.GetBuildingCount(UnitTypeId.NEXUS)
        if baseCount >= 2 and bot.supply_used < 90:
            return
        if bot.startingGame_rusherBuilt < 2:
            return
        if (
            baseCount < self.target_Base_Count
            and bot.supply_workers
            >= bot.townhalls.amount * self.workerCapPerTownhall - 5
        ):
            if bot.can_afford(UnitTypeId.NEXUS):
                await bot.expand_now()
