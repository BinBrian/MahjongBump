from typing import Dict, List, Tuple, Optional, Type
from enum import auto

import time
import enum
import typing
import random

import sys


class Logger:
    level = 2

    def __init__(self, moduleName):
        self.moduleName = moduleName

    def Trace(self, text):
        if self.level > 0:
            return
        print(f"[TRACE][{self.moduleName}]{text}", file=sys.stdout, flush=True)

    def Debug(self, text):
        if self.level > 1:
            return
        print(f"[DEBUG][{self.moduleName}]{text}", file=sys.stdout, flush=True)

    def Info(self, text):
        print(f"[INFO][{self.moduleName}]{text}", file=sys.stdout, flush=True)

    def Warn(self, text):
        print(f"[WARN][{self.moduleName}]{text}", file=sys.stdout, flush=True)

    def Error(self, text):
        print(f"[ERROR][{self.moduleName}]{text}", file=sys.stderr, flush=True)


SysLog = Logger("ECS")


# 组件
class Component:

    def __init__(self):
        self.entity = None

    def Start(self, entity):
        self.entity = entity

    def Destroy(self):
        self.entity = None


# 单例组件
class SingletonComponent(Component):

    def __init__(self, compCls):
        super(SingletonComponent, self).__init__()
        self.linkTy = compCls

    # 单例实体特殊处理, 常规写法无需考虑单例销毁
    def Start(self, entity):
        super(SingletonComponent, self).Start(entity)
        self.entity.world.singletons[self.linkTy] = self.entity.GetComponent(self.linkTy)

    def Destroy(self):
        self.entity.world.singletons.pop(self.linkTy)
        super(SingletonComponent, self).Destroy()


# 实体
class Entity:
    def __init__(self, world):
        self.world = world
        self.eID = 0
        self.components: Dict[Type[Component], Component] = {}

    def AddComponent(self, comp: Component):
        comp.Start(self)
        self.components[comp.__class__] = comp

    def GetComponent(self, compCls: Type[Component]) -> typing.Union[None, Component, typing.Any]:
        return self.components.get(compCls, None)

    def HasComponent(self, compCls: Type[Component]) -> bool:
        return compCls in self.components

    def RemoveComponent(self, compCls: Type[Component]):
        if comp := self.components.pop(compCls, None):
            comp.Destroy()

    def Destroy(self):
        for compTy in list(self.components.keys()):
            self.RemoveComponent(compTy)
        self.world = None


class System:
    def __init__(self, world):
        self.world = world

    def Update(self):
        pass


class World:
    def __init__(self, name: str = "Default"):
        self.name = name
        self.entities: Dict[int, Entity] = {}
        self._nextID = 0
        self.singletons: Dict[Type[Component], Component] = {}

    def Start(self):
        pass

    def Destroy(self):
        for entity in list(self.entities.values()):
            self.RemoveEntity(entity)

    def _GenID(self) -> int:
        self._nextID += 1
        return self._nextID

    def GetSingleton(self, compCls: Type[Component]) -> Optional[Component]:
        return self.singletons.get(compCls, None)

    def CreateSingleton(self, comp: Component):
        if comp.__class__ in self.singletons:
            return
        entity = self.CreateEntity()
        entity.AddComponent(comp)
        entity.AddComponent(SingletonComponent(comp.__class__))

    def CreateEntity(self):
        entity = Entity(self)
        self.AddEntity(entity)
        return entity

    def GetEntity(self, eID: int) -> Entity:
        return self.entities.get(eID, None)

    def AddEntity(self, entity: Entity):
        entity.eID = self._GenID()
        SysLog.Trace(f"World.AddEntity world:{self.name} eid:{entity.eID} comps:{list(entity.components.keys())}")
        self.entities[entity.eID] = entity

    def RemoveEntity(self, entity: Entity):
        if entity.world is not self:
            return
        SysLog.Trace(f"World.RemoveEntity world:{self.name} eid:{entity.eID} comps:{list(entity.components.keys())}")
        entity.Destroy()
        del self.entities[entity.eID]

    def RemoveEntityByID(self, eID: int):
        entity = self.entities.get(eID, None)
        if not entity:
            return
        self.RemoveEntity(entity)

    def GetEntityWithComps(self, comps: List[Type[Component]]) -> List[Entity]:
        lst = []
        for entity in self.entities.values():
            if all([entity.HasComponent(compCls) for compCls in comps]):
                lst.append(entity)
        return lst

    def Update(self):
        pass


# region 游戏状态

@enum.unique
class GameState(enum.Enum):
    INIT = auto()
    FINISH = auto()


class GameStateComponent(Component):

    def __init__(self):
        super(GameStateComponent, self).__init__()
        # self.state = GameState.INIT
        self.drawTimes = 10
        self.cardTy = (SuitType.万子牌, 1)
        self.score = 0


# endregion

# region 麻将牌


@enum.unique
class SuitType(enum.Enum):
    条子牌 = auto()  # 条子
    筒子牌 = auto()  # 筒子
    万子牌 = auto()  # 万子
    风牌 = auto()  # 风色
    箭牌 = auto()  # 箭牌


class CardComponent(Component):

    def __init__(self, suit: SuitType, val):
        super(CardComponent, self).__init__()
        self.suit = suit  # 花色
        self.val = val  # 牌号


# endregion


GameLog = Logger("MahjongBump")


# region Util

class CovertUtil:
    bases = {
        1: "一",
        2: "二",
        3: "三",
        4: "四",
        5: "五",
        6: "六",
        7: "七",
        8: "八",
        9: "九",
    }

    @classmethod
    def An2Cn(cls, num: int) -> str:
        return str(cls.bases.get(num, num))


class MahjongUtil:
    specialSuits = {SuitType.风牌: {1: "东风", 2: "南风", 3: "西风", 4: "北风"},
                    SuitType.箭牌: {1: "红中", 2: "白板", 3: "发财"}}
    basicSuitMaxVal = 9

    @classmethod
    def CardName(cls, suit: SuitType, val: int):
        if suit == SuitType.万子牌:
            return CovertUtil.An2Cn(val) + "万"
        elif suit == SuitType.条子牌:
            return CovertUtil.An2Cn(val) + "条"
        elif suit == SuitType.筒子牌:
            return CovertUtil.An2Cn(val) + "筒"
        elif suit in cls.specialSuits and val in cls.specialSuits[suit]:
            return cls.specialSuits[suit][val]
        return ""

    @classmethod
    def GenerateCards(cls) -> List[Tuple[SuitType, int]]:
        cards = []
        for suitTy in list(SuitType):
            if suitTy in cls.specialSuits:
                for val in cls.specialSuits[suitTy].keys():
                    cards.extend([(suitTy, val)] * 4)
            else:
                for i in range(9):
                    cards.extend([(suitTy, i + 1)] * 4)
        return cards

    @classmethod
    def RandomCard(cls):
        suit = random.choice(list(SuitType))
        if suit not in cls.specialSuits:
            return suit, random.randint(1, cls.basicSuitMaxVal)
        return suit, random.choice(list(cls.specialSuits[suit].keys()))


# endregion


"""

1. 可碰牌和可抓牌: 在ECS来看只是牌实体的状态, 通过增删组件来解耦, 两个行为分别对应牌的可抓取和可碰牌


体验ECS:
1.ECS部分状态逻辑有关联，只能通过Util和System去整合了，整体上还是欠封装的
2.System间协作解耦，可以通过事件，事件应该是一个Entity么? 如此，一次Notify就产生多个事件Entity投放到多个System
事件监听的行为也是状态
"""


# region 播报系统

class ReportMessageManagerComponent(Component):
    def __init__(self):
        super(ReportMessageManagerComponent, self).__init__()
        self.uid = 0
        self.queue = []


class ReportMessageComponent(Component):
    def __init__(self):
        super(ReportMessageComponent, self).__init__()
        self.text = ""


class ReportSystem(System):
    def __init__(self, world):
        super(ReportSystem, self).__init__(world)

    def Update(self):
        reportMgr = self.world.GetSingleton(ReportMessageManagerComponent)
        for msg in reportMgr.queue:
            print(msg)


class ReportUtil:

    @classmethod
    def GetReportUID(cls, reportMgr):
        reportMgr.uid += 1
        return reportMgr.uid

    @classmethod
    def PushReport(cls, reportMgr, action, content):
        reportUID = cls.GetReportUID(reportMgr)
        reportMgr.queue.append("[No.{reportUID}][{action}] {content}".format(reportUID=reportUID, action=action, content=content))

    @classmethod
    def PushDrawActionReport(cls, reportMgr, content):
        cls.PushReport(reportMgr, "抓牌", content)

    @classmethod
    def PushBumpActionReport(cls, reportMgr, content):
        cls.PushReport(reportMgr, "碰牌", content)

    @classmethod
    def PushScoreGainActionReport(cls, reportMgr, content):
        cls.PushReport(reportMgr, "积分", content)


# endregion


# region 抓取系统

class DrawableComponent(Component):
    pass


class DrawingSystem(System):
    def __init__(self, world):
        super(DrawingSystem, self).__init__(world)

    def Update(self):
        gameState = self.world.GetSingleton(GameStateComponent)
        reportMgr = self.world.GetSingleton(ReportMessageManagerComponent)

        if gameState.drawTimes <= 0:
            GameLog.Info(f"MahjongBumpWorld.Update stopped not drawing times running:{False}")
            self.world.running = False  # FIXME: 更优雅的设置退出?
            return

        cards = self.world.GetEntityWithComps([CardComponent, DrawableComponent])

        if not cards:
            GameLog.Info(f"MahjongBumpWorld.Update stopped not enough cards to draw running:{False}")
            self.running = False
            return

        for entity in cards:
            if gameState.drawTimes <= 0:
                break
            cardComp: CardComponent = entity.GetComponent(CardComponent)

            ReportUtil.PushDrawActionReport(reportMgr, f"花色:{MahjongUtil.CardName(cardComp.suit, cardComp.val)} 剩余抽取次数:{gameState.drawTimes - 1} 放入暂存区")
            gameState.drawTimes -= 1
            entity.RemoveComponent(DrawableComponent)
            entity.AddComponent(BumpableComponent())
            if cardComp.suit == gameState.cardTy[0]:
                ReportUtil.PushDrawActionReport(reportMgr, f"花色:{MahjongUtil.CardName(cardComp.suit, cardComp.val)} "
                                                           f"与 *{MahjongUtil.CardName(gameState.cardTy[0], gameState.cardTy[1])} "
                                                           f"同花色 抽取次数+1 剩余抽取次数:{gameState.drawTimes + 1}"
                                                )
                gameState.drawTimes += 1


# endregion

# region 碰牌系统


class BumpableComponent(Component):
    pass


class BumpingSystem(System):
    def __init__(self, world):
        super(BumpingSystem, self).__init__(world)

    def Update(self):
        gameState = self.world.GetSingleton(GameStateComponent)
        reportMgr = self.world.GetSingleton(ReportMessageManagerComponent)
        delCards = set()

        bumps = self.world.GetEntityWithComps([CardComponent, BumpableComponent])

        for cardA in bumps:
            if cardA.eID in delCards:
                continue
            for cardB in bumps:
                if cardB.eID in delCards:
                    continue
                if cardA.eID == cardB.eID:
                    continue

                cardAComp: CardComponent = cardA.GetComponent(CardComponent)
                cardBComp: CardComponent = cardB.GetComponent(CardComponent)

                if (cardAComp.suit, cardAComp.val) == (cardBComp.suit, cardBComp.val):
                    delCards.add(cardA.eID)
                    delCards.add(cardB.eID)
                    ReportUtil.PushBumpActionReport(reportMgr, f"花色:{MahjongUtil.CardName(cardBComp.suit, cardBComp.val)} 抽取次数+1 "
                                                               f"剩余抽取次数:{gameState.drawTimes + 1} 积分:{gameState.score + 1}")
                    gameState.score += 1
                    gameState.drawTimes += 1
                    break

        for eID in delCards:
            self.world.RemoveEntityByID(eID)


# endregion

# region 加载系统

class SetUpSystem(System):
    INIT_DRAW_TIMES = 10  # 基础抽数

    def __init__(self, world):
        super(SetUpSystem, self).__init__(world)

    def Init(self):
        self.InitGameState()
        self.InitReportSys()
        self.InitCards()

    def InitGameState(self):
        gameState = GameStateComponent()
        gameState.drawTimes = self.INIT_DRAW_TIMES
        gameState.cardTy = MahjongUtil.RandomCard()
        self.world.CreateSingleton(gameState)

    def InitReportSys(self):
        reportMgr = ReportMessageManagerComponent()
        self.world.CreateSingleton(reportMgr)

    def InitCards(self):
        for suitTy, val in MahjongUtil.GenerateCards():
            card = self.world.CreateEntity()
            card.AddComponent(CardComponent(suitTy, val))
            card.AddComponent(DrawableComponent())


# endregion


class MahjongBumpWorld(World):

    def __init__(self, name):
        super(MahjongBumpWorld, self).__init__(name)
        self.setUpSystem = SetUpSystem(self)
        self.drawSystem = DrawingSystem(self)
        self.bumpSystem = BumpingSystem(self)
        self.reportSystem = ReportSystem(self)
        self.running = False

    def Start(self):
        self.setUpSystem.Init()
        GameLog.Info(f"MahjongBumpWorld.Started running:{True}")
        self.running = True

    def Update(self):
        GameLog.Debug("MahjongBumpWorld.Update tick")
        # 抓牌
        self.drawSystem.Update()
        # 碰牌
        self.bumpSystem.Update()
        # 播报
        self.reportSystem.Update()
        time.sleep(0.02)


# endregion

gw = MahjongBumpWorld("MahjongBump")
gw.Start()

while gw.running:
    gw.Update()

gw.Destroy()
