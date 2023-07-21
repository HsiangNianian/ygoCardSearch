# -*- encoding: utf-8 -*-
'''
     ██╗██╗   ██╗██╗   ██╗███╗   ██╗██╗  ██╗ ██████╗ 
     ██║╚██╗ ██╔╝██║   ██║████╗  ██║██║ ██╔╝██╔═══██╗
     ██║ ╚████╔╝ ██║   ██║██╔██╗ ██║█████╔╝ ██║   ██║
██   ██║  ╚██╔╝  ██║   ██║██║╚██╗██║██╔═██╗ ██║   ██║
╚█████╔╝   ██║   ╚██████╔╝██║ ╚████║██║  ██╗╚██████╔╝
 ╚════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ 
                                                     
    Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import OlivOS
import OlivaDiceCore
import ygoCardSearch
import requests
import random
import re
import os

os.environ['NO_PROXY'] = 'ygocdb.com,ss.jyunko.cn'


class Event(object):
    def init(self, Proc):
        pass

    def private_message(self, Proc):
        reply(self, Proc)

    def group_message(self, Proc):
        reply(self, Proc)

    def poke(self, Proc):
        pass

    def save(self, Proc):
        pass

    def menu(self, Proc):
        pass


def RandomCard():
    cardListUrl = 'https://ss.jyunko.cn/assets/ygoCardIDList'
    cardList = requests.get(cardListUrl).text
    idList1 = re.sub('[^\d\n]', ' ', cardList).split()
    idList2 = [
        idList1[ele] for ele in range(len(idList1)) if len(idList1[ele]) == 8
    ]
    id = idList2[random.randint(1, len(idList2))]
    detailsURL = f'https://ygocdb.com/card/{id}#faq'
    imgUrl = requests.get(detailsURL)
    # TODO(简律纯/2022年12月8日): 未来(下个版本)或许会完善随机出卡信息的匹配。
    img = re.search(r'(https://.*\.jpg)',
                    imgUrl.text, re.M | re.I).group()  # type: ignore
    Name = re.sub(
        '(<span>|</span>)',
        '',
        re.search(
            r'(<span>(.*)</span>)', imgUrl.text, re.M | re.I  # type: ignore
        )[1],
    )
    # cardDesc = re.search(r'<(.*)class="desc">(.*)</div>',imgUrl.text,re.M|re.I).group(1)
    # jsn = requests.get('https://ygocdb.com/api/vo/>search='+Name).json()
    # cardDesc = jsn['result'][0]['text']['desc']
    Desc = re.findall(r'<div\sclass=\"desc\">([^\<]+)', imgUrl.text)[0]
    return Name+Desc+'[CQ:image,file='+img+']'


def reply(plugin_event, Proc):
    ITEM_LIST = plugin_event.data.message.split()
    if ITEM_LIST[0] == ".ygo" and ITEM_LIST[1] in ['search', 's']:
        '''轮询查卡

        实现:【.ygo s|search】'''
        URL = f'https://ygocdb.com/api/v0/?search={ITEM_LIST[2]}'
        JSON_DATA = requests.get(URL).json()
        if len(JSON_DATA['result']) == 0:
            plugin_event.reply('找不到这张卡哦...换个关键词吧~')
        else:
            tmp_reply_str = ''  # '等待输入编号...\n若需继续查询请输入要查询的编号。\n回复【退出查询】可退出查询。'

            # ==============================================
            # 请勿多次使用【.ygo s|search】命令 !!!
            # TODO(简律纯/2022年12月8日): 实现阶段限制的issue.
            # ==============================================
            while True:
                '''等待查询

                引用:@仑质的OlivaDiceCore模块'''
                flag = False

                if plugin_event != None:
                    indexNum = 5
                    txt = ''
                    # while(len(JSON_DATA['result'])-1-indexNum > 0):
                    if len(JSON_DATA['result']) > 5:
                        for i in range(5):
                            txt = (
                                f'{str(i)}.'
                                + str(JSON_DATA['result'][i]['id'])
                                + ':'
                                + JSON_DATA['result'][i]['cn_name']
                                + '\n'
                                + txt
                            )
                    else:
                        for i in range(len(JSON_DATA['result'])):
                            txt = (
                                f'{str(i)}.'
                                + str(JSON_DATA['result'][i]['id'])
                                + ':'
                                + JSON_DATA['result'][i]['cn_name']
                                + '\n'
                                + txt
                            )
                    plugin_event.reply(
                        '共匹配'+str(len(JSON_DATA['result'])) +
                        '张，列出以下匹配度最高的待选卡:\n'+txt +
                        '输入要查看的编号:'
                    )
                    if flag := True:
                        OlivaDiceCore.msgReply.replyMsg(
                            plugin_event, tmp_reply_str)
                        tmp_select: 'str|None' = OlivaDiceCore.msgReplyModel.replyCONTEXT_regWait(
                            plugin_event=plugin_event,
                            flagBlock='allowCommand',
                            hash=OlivaDiceCore.msgReplyModel.contextRegHash(
                                [None, plugin_event.data.user_id])
                        )
                        if type(tmp_select) == str and tmp_select.isdigit():  # type: ignore
                            index = int(tmp_select)  # type: ignore
                            id = JSON_DATA['result'][index]['id']
                            cn_name = JSON_DATA['result'][index]['cn_name']
                            jp_ruby = JSON_DATA['result'][index]['jp_ruby']
                            textTypes = JSON_DATA['result'][index]['text']['types']
                            # textPdesc = JSON_DATA['result'][0]['text']['pdesc']
                            textDesc = JSON_DATA['result'][index]['text']['desc']
                            detailsURL = f'https://ygocdb.com/card/{str(id)}#faq'
                            imgUrl = requests.get(detailsURL)
                            img = re.search(r'(https://.*\.jpg)',
                                            imgUrl.text, re.M | re.I).group()
                            result = (
                                f'中文名:{cn_name}'
                                + '\n日文名:'
                                + jp_ruby
                                + '\n卡片密码:'
                                + str(id)
                                + '\n卡片种类:'
                                + textTypes
                                + '\n'
                                + textDesc
                                + '[CQ:image,file='
                                + img
                                + ']'
                            )
                            plugin_event.reply(result)
                                                    # flag = False
                        elif type(tmp_select) == str and tmp_select == '退出查询':
                            plugin_event.reply('已退出~\n嘶~看来是找到了想要查询的卡片呢——')
                            flag = False
                        else:
                            plugin_event.reply('未查询到匹配条目')
                        break
    elif ITEM_LIST[0] == '.ygo' and ITEM_LIST[1] in ['r', 'random']:
        '''随机抽卡

        实现:【.ygo r|random】'''
        # @see RandomCatd()
        try:
            times = ITEM_LIST[2]
        except IndexError:
            times = 1
        if times > 5:  # type: ignore
            plugin_event.reply('输入数目超过上限(5)！')
        else:
            plugin_event.reply(f'随机抽取{times}张卡ing...')
            for _ in range(times):
                plugin_event.reply(RandomCard())


# txt = '''
# <div class="desc">
# [怪兽|效果|灵摆] 魔法师/光<br>[★4] 1800/400  8/8
# <hr>
# ①：1回合1次，怪兽之间进行战斗的伤害步骤开始时才能发动。这张卡回到持有者手卡，从卡组把1张魔法卡除外。自己怪兽不会被那次战斗破坏，那次战斗发生的对自己的战斗伤害变成一半。
# <hr>
# ①：这张卡给与对方战斗伤害时才能发动。从卡组把1只「<a href="/?search=霸王眷龙" target="_blank" class="search">霸王眷龙</a>」怪兽或者「<a href="/?search=霸王门" target="_blank" class="search">霸王门</a>」怪兽或者1张「<a href="/card/92428405" data-refer="92428405" data-toggle="tooltip" target="_blank" data-original-title="" title="">霸王龙之魂</a>」加入手卡。<br>②：自己·对方的准备阶段发动。双方各自可以从自身卡组把1张魔法卡除外。<br>③：1回合1次，自己或者对方的怪兽的攻击宣言时发动。被攻击的玩家可以让以下效果适用。<br>●选除外的1张自身的魔法卡加入手卡。那之后，那张卡丢弃，那次攻击无效。
# </div>
# '''
# print(re.findall(r'<div\sclass=\"desc\">([^\<]+)',txt)[0])
