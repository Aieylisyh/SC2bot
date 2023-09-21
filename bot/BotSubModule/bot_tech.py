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


class bot_tech:
    bot: BotAI

    def __init__(self, bot: BotAI):
        self.bot = bot

    # method to research the upgrades at the forge
    async def forge_research(self):
        # Research warp gate if cybercore is completed
        if (
            self.bot.structures(UnitTypeId.CYBERNETICSCORE).ready
            and self.bot.can_afford(AbilityId.RESEARCH_WARPGATE)
            and self.bot.already_pending_upgrade(UpgradeId.WARPGATERESEARCH) == 0
            and self.bot.startingGame_rusherBuilt >= 2
        ):
            ccore = self.bot.structures(UnitTypeId.CYBERNETICSCORE).ready.first
            ccore.research(UpgradeId.WARPGATERESEARCH)
        # Research blink if VC is completed
        if (
            self.bot.structures(UnitTypeId.TWILIGHTCOUNCIL).ready
            and self.bot.can_afford(AbilityId.RESEARCH_BLINK)
            and self.bot.already_pending_upgrade(UpgradeId.BLINKTECH) == 0
        ):
            vc = self.bot.structures(UnitTypeId.TWILIGHTCOUNCIL).ready.first
            vc.research(UpgradeId.BLINKTECH)

        if (
            self.bot.structures(UnitTypeId.TWILIGHTCOUNCIL).ready
            and self.bot.can_afford(AbilityId.RESEARCH_CHARGE)
            and self.bot.already_pending_upgrade(UpgradeId.CHARGE) == 0
            and self.bot.already_pending_upgrade(UpgradeId.BLINKTECH) == 1
        ):
            vc = self.bot.structures(UnitTypeId.TWILIGHTCOUNCIL).ready.first
            vc.research(UpgradeId.CHARGE)

        if self.bot.structures(UnitTypeId.FORGE).ready:
            # we get our forge and if we can afford and not already upgrading we cycle through the upgrades until lvl 2
            forge = self.bot.structures(UnitTypeId.FORGE).ready.first
            nexuses = self.bot.structures(UnitTypeId.NEXUS).ready
            if not forge.is_idle:
                for loop_nexus in nexuses:
                    if loop_nexus.energy >= 50:
                        loop_nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, forge)
                        break

            if (
                self.bot.can_afford(AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1)
                and self.bot.already_pending_upgrade(
                    UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1
                )
                == 0
                and forge.is_idle
            ):
                forge.research(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1)
            elif (
                self.bot.can_afford(AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1)
                and self.bot.already_pending_upgrade(
                    UpgradeId.PROTOSSGROUNDARMORSLEVEL1
                )
                == 0
                and forge.is_idle
            ):
                forge.research(UpgradeId.PROTOSSGROUNDARMORSLEVEL1)
            elif (
                self.bot.can_afford(AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL1)
                and self.bot.already_pending_upgrade(UpgradeId.PROTOSSSHIELDSLEVEL1)
                == 0
                and forge.is_idle
            ):
                forge.research(UpgradeId.PROTOSSSHIELDSLEVEL1)
            elif (
                self.bot.can_afford(AbilityId.FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL2)
                and self.bot.already_pending_upgrade(
                    UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2
                )
                == 0
                and forge.is_idle
            ):
                forge.research(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2)
            elif (
                self.bot.can_afford(AbilityId.FORGERESEARCH_PROTOSSGROUNDARMORLEVEL2)
                and self.bot.already_pending_upgrade(
                    UpgradeId.PROTOSSGROUNDARMORSLEVEL2
                )
                == 0
                and forge.is_idle
            ):
                forge.research(UpgradeId.PROTOSSGROUNDARMORSLEVEL2)
            elif (
                self.bot.can_afford(AbilityId.FORGERESEARCH_PROTOSSSHIELDSLEVEL2)
                and self.bot.already_pending_upgrade(UpgradeId.PROTOSSSHIELDSLEVEL2)
                == 0
                and forge.is_idle
            ):
                forge.research(UpgradeId.PROTOSSSHIELDSLEVEL2)
