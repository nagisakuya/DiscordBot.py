#!/usr/bin/env python3


import discord
import random
import math
import asyncio
import os
import subprocess
from mutagen.mp3 import MP3
import soundfile
from collections import deque

def mutagen_length(path):
    try:
        audio = MP3(path)
        length = audio.info.length
        return length
    except:
        return None

def jtalk(text,output_path = os.path.join(os.path.dirname(__file__),'open_jtalk.wav')):
    OPENJTALK_BINPATH = '/usr/local/bin'
    OPENJTALK_DICPATH = '/usr/local/share/open_jtalk/open_jtalk_dic_utf_8-1.10'
    OPENJTALK_VOICEPATH = '/usr/local/share/hts_voice/mei/mei_normal.htsvoice'
    open_jtalk=[OPENJTALK_BINPATH + '/open_jtalk']
    mech=['-x',OPENJTALK_DICPATH]
    htsvoice=['-m',OPENJTALK_VOICEPATH]
    speed=['-r','0.6']
    outwav=['-ow',output_path]
    cmd=open_jtalk+mech+htsvoice+speed+outwav
    c = subprocess.Popen(cmd,stdin=subprocess.PIPE)
    c.stdin.write(text.encode('UTF-8'))
    c.stdin.close()
    c.wait()
    return output_path

def is_mention(str):
    return len(str) == 21 and str.find("<@") == 0 and str.find(">") == 20

def get_speaking_members(members):
    return list(filter(lambda m:m.voice != None,members))

def is_speaking(member):
    return True if member.voice != None else False

class Managed():
    managed_objects = []
    def __init__(self):
        raise NotImplementedError("Use create method")
    def __new__(cls):
        self = object.__new__(cls)
        Managed.managed_objects.append(self)
        return self
    def __del__(self):
        Managed.managed_objects.remove(self)
    async def remove(self):
        pass
    async def deleate(self):
        pass
    async def call_on_voice_state_update(self,member, before, after):
        pass
    async def call_on_message(self,message):
        pass
    @classmethod
    async def at_exit(cls):
        for obj in Managed.managed_objects:
            await obj.deleate()
    @classmethod
    async def create(cls,base):
        self = cls.__new__()
        return self

class Managed_Voice_Channel(Managed):
    name = "VoiceChannel"
    async def remove(self):
        await self.voice_channel.delete()
        super().__del__()
    async def deleate(self):
        await self.voice_channel.delete()
    async def move_here(self,member):
        if (is_speaking(member) and member.guild == self.voice_channel.guild and member.voice.channel != self.voice_channel):
            await member.move_to(self.voice_channel)
    async def remove_if_empty(self):
        if not list(filter(lambda m:m.bot == False,self.voice_channel.members)):
            await self.remove()
    @classmethod
    async def create(cls,guild, *,name=None, overwrites=None, category=None, reason=None, **options):
        self = super().__new__(cls)
        self.voice_channel = await guild.create_voice_channel(cls.name if name == None else name, overwrites=overwrites, category=category, reason=reason, **options)
        return self

class Sexroom(Managed_Voice_Channel):
    name = "〇ックスしないと出られない部屋"
    async def call_on_voice_state_update(self,member, before, after):
        return await self.remove_if_empty()
    @classmethod
    async def create(cls,message):
        guild = message.guild
        speaking_members = get_speaking_members(guild.members)
        if len(speaking_members) > 0:
            target = random.choice(speaking_members)
            self = await super().create(guild ,category = target.voice.channel.category,limit = 2)
            await self.move_here(target)
            if len(speaking_members) == 1:
                voice_client = await self.voice_channel.connect()
                print("connectted to sexroom")
            else:
                speaking_members.remove(target)
                await self.move_here(random.choice(speaking_members))
        else:
            await message.channel.send("*しかし誰も来なかった")
            return None
        return self

class Blackhole(Managed_Voice_Channel):
    name = "ブラックホール"
    async def call_on_voice_state_update(self,member, before, after):
        await self.move_here(member)
        return False
    @classmethod
    async def create(cls,guild ,category):
        self = await super().create(guild ,category = category)
        for member in get_speaking_members(self.voice_channel.guild.members):
            await self.move_here(member)
        return self

class Managed_Voice_Client(Managed):
    voice_client = None
    async def remove(self):
        await Managed_Voice_Client.disconnect()
        super().__del__()
    async def move_to(self,voice_channel):
       if voice_channel != voice_client.channel:
           await voice_client.move_to(voice_channel)
    async def deleate(self):
        await Managed_Voice_Client.disconnect()
    @classmethod
    async def create(cls,voice_channel,*, timeout=None, reconnect=True):
        if Managed_Voice_Client.voice_client != None:
            await disconnect()
            managed_objects.pop(managed_objects.index(self))
        self = super().__new__(cls)
        Managed_Voice_Client.voice_client = await voice_channel.connect(timeout =timeout,reconnect = reconnect)
        return self
    @classmethod
    async def disconnect(cls):
        if Managed_Voice_Client.voice_client != None:
            await Managed_Voice_Client.voice_client.disconnect()
            cls.voice_client = None

class Stalker(Managed_Voice_Client):
    async def call_on_voice_state_update(self,member, before, after):
        if hasattr(self,'target') and self.target == member and self.target.voice != None:
                await self.move_to(self.target.voice.channel)
    @classmethod
    async def create(cls,member):
        if member.voice != None:
            self = await super().create(member.voice.channel)
            self.target = member
        return self

class Speaker(Managed_Voice_Client):
    chatonly_members = []
    queue = deque()
    is_speaking = False
    async def call_on_message(self,message):
        url = 0
        while url != -1:
            url = message.content.find("https://")
            if url != -1:
                length = message.content[url :].find(" ")
                message.content = message.content[0 : url] + "URL" + message.content[ end  if end != -1 else -0:]
        if message.author in self.chatonly_members:
            self.queue.append(message.content)
            if not self.is_speaking:
                await self.read()
    async def read(self):
        self.is_speaking = True
        while len(self.queue) > 0:
            wav = jtalk(self.queue.popleft())
            tmp = soundfile.SoundFile(wav)
            length = len(tmp)/tmp.samplerate
            Managed_Voice_Client.voice_client.play(discord.FFmpegPCMAudio(wav))
            await asyncio.sleep(length)
        self.is_speaking = False
    @classmethod
    async def create(cls,member):
        if member.voice != None:
            self = await super().create(member.voice.channel)
            self.chatonly_members.append(member)
        return self


bot = discord.Client(intents = discord.Intents.all())

@bot.event
async def on_ready():
    print('Logged in')
    #await bot.get_channel(476344593508728835).send('watchinpo参上!!\n/hでヘルプを表示します')
@bot.event
async def on_voice_state_update(member, before, after):
    for obj in Managed.managed_objects:
        await obj.call_on_voice_state_update(member, before, after)


@bot.event
async def on_message(message):
    print(message.content)
    if message.author.bot:
        #print("message from bot")
        return
    message_list = message.content.split()
    if message_list[0] == '/h':
        print('help called')
        await message.channel.send('''
        /help さらに詳細なヘルプを表示します
        /summon 茶寮を召喚します
        /roll 100面ダイスを振ります
        /flip コインを投げます
        /mute watchingを強制ミュートします
        /unmute ミュート解除
        /sex ？？？
        /blackhole ？？？
        /speak チャット欄に打ち込んだ内容を喋ってくれます
        /bye ボイスチャンネルのbotに別れを告げます
        ''')
    elif message_list[0] == '/help':
        print('help called')
        await message.channel.send('''
        /summon <member=茶寮> memberを召喚します
        /roll <number=100> <subnumber=100> number面ダイスを振ります 引数が二つある場合は二つの引数の間からロールされます
        /sex セックスできない部屋を作り、ランダムに二人をその部屋に入れます
        /blackhole 全てを吸い込むブラックホールを召喚します
        ''')
    elif message_list[0] == '/summon':
        print('summon called')
        if len(message_list) == 1:
            target = "<@353199430687653898>"
        elif is_mention(message_list[1]):
            target = message_list[1]
        else:
            target = discord.utils.find(lambda m: m.name == message_list[1], message.guild.members)
            if target == None:
                await message.channel.send('そんな人しらなーいヽ(`Д´)ﾉ')
                return
            target = target.mention
        await message.channel.send(f'༽୧༺ ‡۞卍✞༒ {target} ༒✞卍۞‡༻୨༼')
    elif message_list[0] == '/roll':
        if len(message_list) == 2:
            min = 1
            max = int(message_list[1])
        elif len(message_list) == 3:
            min = int(message_list[1])
            max = int(message_list[2])
            if min > max:
                min , max = max , min
        else:
            min = 1
            max = 100
        if message.author.id == 241192743345455105:
            print('roll called by watching')
            result = int(math.sqrt(random.randint(min ** 2,(max + 1) ** 2 - 1)))
        else:
            print('roll called')
            result = random.randint(min,max)
        if min == 1:
            await message.channel.send(f'{message.author.mention} が{max}面ダイスを振った...{result}！')
        else:
            await message.channel.send(f'{message.author.mention} のために{min}から{max}までの数字を一つ適当に選んだ...{result}！')
    elif message_list[0] == '/flip':
        await message.channel.send(f'{message.author.mention} がコインを投げた...{"表" if random.getrandbits(1) == 0 else "裏"}！')
    elif message_list[0] == '/mute':
        watching = message.guild.get_member(241192743345455105)
        if watching is not None:
            await message.channel.send(f'{random.choice(["黙れ小僧！","サイレンス","シャラップ！","封印！","#騒音被害者の会","watchingが泣いてるよ (つд⊂)ｴｰﾝ","(ファミチキください)"])}')
            await watching.edit(mute=True)
    elif message_list[0] == '/unmute':
        watching = message.guild.get_member(241192743345455105)
        if watching is not None:
            await message.channel.send(f'{random.choice(["反省したみたいだしもう許してあげない？","封印解除！","我を封印したこと後悔させてやろう","watching、復活！","ひゃっはー！復旧したぜー！！"])}')
            await watching.edit(mute=False)
    elif message_list[0] == '/sex':
        await Sexroom.create(message)
    elif message_list[0] == '/blackhole':
        await Blackhole.create(message.guild, message.author.voice.channel.category if message.author.voice != None else None)
    elif message_list[0] == '/speak':
        await Speaker.create(message.author)        
        await message.channel.send(f"{message.author.mention}の書いたことを喋ります！！")
    elif message_list[0] == '/bye':
        await Managed_Voice_Client.disconnect()
        await message.channel.send(f"さようなら")
    else:
        for obj in Managed.managed_objects:
            await obj.call_on_message(message)
        return
    await message.delete()


def shutdown():
    print("shutdown...")
    bot.loop.run_until_complete(Managed.at_exit())
    bot.loop.run_until_complete(bot.logout())

def main():
    f = open(os.path.join(os.path.dirname(__file__),"Token.txt"))
    TOKEN = f.read()
    f.close()
    try:
        bot.loop.run_until_complete(bot.start(TOKEN))
    except Exception:
        shutdown()
    finally:
        shutdown()

if __name__ == '__main__':
        main()
