"""
基础概念
抓牌行为: 从池中抓牌，每抓取一张，放入暂存区并则判断基础花色。若抓牌花色与指定花色一致，则继续抓牌。以下简称"抓取"或"抓牌"
抽取池(区): 所有牌子来源
暂存区: 临时存放抓牌的牌子
碰子区: 存放匹配的碰子
对对碰: 计算暂存区中的所有匹配的牌面花色，每匹配X对牌，则执行X次抓牌

基本规则
1. 开局阶段: 随机选一个基础花色(条子、风色、筒子，万子), 以及从池中抓取若干张牌(一般初始10张牌)
2. 流程阶段: 当抓取行为结束时才进行对对碰，直到抽取池清空或暂存区不再满足对对碰条件时，游戏结束；按照这个游戏规则下，如何调整来增加玩家的参与感和爽感？

"""

from typing import List, Dict, Optional

import copy
import enum
import random


@enum.unique
class BasicCardType(enum.Enum):
    万子牌 = 0
    条子牌 = 1 << 0
    筒子牌 = 1 << 1
    风牌 = 1 << 2
    箭牌 = 1 << 3


def MarkCardType(basicTy: BasicCardType, offset) -> int:
    return (basicTy.value << 4) + offset


@enum.unique
class CardType(enum.Enum):
    一万 = MarkCardType(BasicCardType.万子牌, 0)
    二万 = MarkCardType(BasicCardType.万子牌, 1)
    三万 = MarkCardType(BasicCardType.万子牌, 2)
    四万 = MarkCardType(BasicCardType.万子牌, 3)
    五万 = MarkCardType(BasicCardType.万子牌, 4)
    六万 = MarkCardType(BasicCardType.万子牌, 5)
    七万 = MarkCardType(BasicCardType.万子牌, 6)
    八万 = MarkCardType(BasicCardType.万子牌, 7)
    九万 = MarkCardType(BasicCardType.万子牌, 8)

    一条 = MarkCardType(BasicCardType.条子牌, 0)
    二条 = MarkCardType(BasicCardType.条子牌, 1)
    三条 = MarkCardType(BasicCardType.条子牌, 2)
    四条 = MarkCardType(BasicCardType.条子牌, 3)
    五条 = MarkCardType(BasicCardType.条子牌, 4)
    六条 = MarkCardType(BasicCardType.条子牌, 5)
    七条 = MarkCardType(BasicCardType.条子牌, 6)
    八条 = MarkCardType(BasicCardType.条子牌, 7)
    九条 = MarkCardType(BasicCardType.条子牌, 8)

    一筒 = MarkCardType(BasicCardType.筒子牌, 0)
    二筒 = MarkCardType(BasicCardType.筒子牌, 1)
    三筒 = MarkCardType(BasicCardType.筒子牌, 2)
    四筒 = MarkCardType(BasicCardType.筒子牌, 3)
    五筒 = MarkCardType(BasicCardType.筒子牌, 4)
    六筒 = MarkCardType(BasicCardType.筒子牌, 5)
    七筒 = MarkCardType(BasicCardType.筒子牌, 6)
    八筒 = MarkCardType(BasicCardType.筒子牌, 7)
    九筒 = MarkCardType(BasicCardType.筒子牌, 8)

    东风 = MarkCardType(BasicCardType.风牌, 0)
    南风 = MarkCardType(BasicCardType.风牌, 1)
    西风 = MarkCardType(BasicCardType.风牌, 2)
    北风 = MarkCardType(BasicCardType.风牌, 3)

    红中 = MarkCardType(BasicCardType.箭牌, 0)
    白板 = MarkCardType(BasicCardType.箭牌, 1)
    发财 = MarkCardType(BasicCardType.箭牌, 2)


MAHJONG_POOL = []
for _cardTy in list(CardType):
    for _ in range(4):
        MAHJONG_POOL.append(_cardTy)


class CardPool:
    def __init__(self):
        self._pool = copy.copy(MAHJONG_POOL)
        random.shuffle(self._pool)
        self._offset = 0

    def Draw(self, n) -> List[CardType]:
        if self.IsEmpty():
            return []
        lst = self._pool[self._offset:self._offset + n]
        self._offset += n
        return lst

    def IsEmpty(self):
        return self._offset >= len(self._pool)

    def GetCount(self) -> int:
        return len(self._pool) - self._offset


class TempStoreArea:
    def __init__(self):
        self._cards: Dict[CardType, int] = {}

    def Enter(self, cards: List[CardType]):
        for cardTy in cards:
            self._cards[cardTy] = self._cards.get(cardTy, 0) + 1

    def ExtractCombos(self) -> List[CardType]:
        lst = []
        for cardTy, count in self._cards.items():
            combo = count // 2
            self._cards[cardTy] -= combo * 2
            lst.extend([cardTy] * combo)
        return lst

    def IsExistCombos(self) -> bool:
        for cardTy, count in self._cards.items():
            if count >= 2:
                return True
        return False

    def GetCount(self) -> int:
        count = 0
        for cnt in self._cards.values():
            count += cnt
        return count


class ComboArea:
    def __init__(self):
        self._combos = {}
        self._comboUID = 0

    def NextUID(self):
        self._comboUID += 1
        return self._comboUID

    def MarkCombo(self, cardType: CardType):
        uid = self.NextUID()
        print(f"ComboArea uid:{uid} card:{cardType.name}")
        self._combos[uid] = cardType

    def GetComboCount(self) -> int:
        return self._comboUID


class ReportManager:
    def __init__(self):
        pass


class Event:
    def __init__(self):
        self._listeners = []


class PubSub:
    def __init__(self):
        self._events = {}

    def Attach(self, ev, listener):
        pass

    def Detach(self, ev, listener):
        pass

    def Notify(self, ev, info):
        pass


class GameStatus(enum.Enum):
    IDLE = 0
    STARTED = 1
    OVER = 2


class World:
    def __init__(self):
        self._pool = CardPool()
        self._comboArea = ComboArea()
        self._tempStore = TempStoreArea()
        self.key: Optional[CardType] = None
        self.status = GameStatus.IDLE
        self.pickCnt = 0

    def OnGameStart(self):
        cards = self._pool.Draw(20)
        print(f"World.OnGameStart cards:{cards}")
        self._tempStore.Enter(cards)

    def Select(self, key: CardType):
        print(f"World.Select key:{key}")
        self.key = key

    def DoBump(self):
        combos = self._tempStore.ExtractCombos()
        if not combos:
            return
        print(f"World.DoBump pick:{self.pickCnt} add:{len(combos)}")
        self.pickCnt += len(combos)
        for cardTy in combos:
            self._comboArea.MarkCombo(cardTy)

    def Run(self):
        assert self.key is not None
        if self.status == GameStatus.IDLE:
            self.OnGameStart()
            self.status = GameStatus.STARTED

        while self.status != GameStatus.OVER:
            while self.pickCnt > 0:
                hits = self._pool.Draw(1)
                if not hits:  # 抽完了
                    break
                cardTy = hits[0]
                addPick = int((cardTy.value >> 4) == (self.key.value >> 4))
                delPick = 1
                newPick = self.pickCnt - delPick + addPick
                print(f"Pick card:{cardTy.name} basic:{BasicCardType(cardTy.value >> 4).name} pick:{newPick} addpick:{addPick} delpick:{delPick}")
                self._tempStore.Enter([cardTy])
                self.pickCnt = newPick

            self.DoBump()

            # if self._tempStore.IsExistCombos():
            #     continue
            if self.pickCnt > 0 and not self._pool.IsEmpty():
                continue
            print(f"World.Run status:{GameStatus.OVER}")
            self.status = GameStatus.OVER

        # GameOver

        print(f"World.Run Done key:{self.key} pick:{self.pickCnt} combos:{self._comboArea.GetComboCount()} temp:{self._tempStore.GetCount()} pool:{self._pool.GetCount()}")

# TODO: 改造为ECS验证一下
if __name__ == '__main__':
    w = World()
    w.Select(random.choice(MAHJONG_POOL))

    # w.Select(CardType.一万)
    w.Run()
