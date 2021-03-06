from octobot.events import bind_event, fire_event
from octobot.plugins import Plugin

import re
from os.path import isfile
import json
from urllib.parse import urlencode
from urllib.request import urlopen
import base64
from io import BytesIO

from PIL import Image


class TestingPlugin(Plugin):
    def __init__(self):
        self.llamaHandler = LlamaHandler()

    @bind_event("plugin_load")
    def plugin_load(self, *, event=None):
        yield from fire_event('command-register', command='llamafy', description='Llama text', helpmsg=',llamafy message')

    @bind_event("command", "llamafy")
    def llamafy(self, sender=None, target=None, args=None, *, event=None):
        print ("entering llama land")
        message = ' '.join(args)
        message = re.sub(r"[^A-Za-z\!\?\. ]", '', message).lower()

        if target.startswith('#'):
            t = target
        else:
            t = sender[0]

        if message:
            llamaURL = self.llamaHandler.llamaItUp(message)
            reply = "%s: %s" % (sender[0], llamaURL)
        else:
            reply = sendingNick + ": Sorry, only letters, full stops, exclamation marks and question marks can be llamafied"

        print ("reply:{}".format(reply))

        yield from fire_event('bot', 'privmsg', target=t, message=reply)


class Imgur():
    def __init__(self, apiKey):
        self.API_KEY = apiKey
        self.API_URL = "http://api.imgur.com/2/"
    
    def upload(self, image, title):
        imageAsFile = BytesIO()
        image.save(imageAsFile, "PNG")
        
        callData = urlencode({
                            "key"  :self.API_KEY,
                            "image":base64.b64encode(imageAsFile.getvalue()),
                            "title": title
                             })
        callData = callData.encode('utf-8')
        
        reply = urlopen(self.API_URL+"upload.json", callData).readall().decode('utf-8')
        if reply:
            return json.loads(reply)
        else:
            return None

    def stats(self, timePeriod = "month"):
        callData = urlencode({"view": timePeriod})
        reply = urlopen(self.API_URL+"stats.json?"+callData).readall().decode('utf-8')
        if reply:
            return json.loads(reply)
        else:
            return None

    def imageInfo(self, hash):
        reply = urlopen(self.API_URL+"image/"+hash+".json").readall().decode('utf-8')
        if reply:
            return json.loads(reply)
        else:
            return None

    def imageDelete(self, hash):
        reply = urlopen(self.API_URL+"delete/"+hash+".json").readall().decode('utf-8')
        if reply:
            return json.loads(reply)        
        else:
            return None



class LlamaHandler():
    def __init__(self):
        self.llama = LlamaText()
        self.previousWords = dict()
        self.wordsFileName = "plugins/llamaFont/previousWords.list"
        self.imgurAPIKey = "ADD ONE"

        if isfile(self.wordsFileName):
            previousWordsFile = open(self.wordsFileName, 'r')
            for line in previousWordsFile:
                line = line.split(";")
                word = line[0]
                url = line[1]
                deleteHash = line[2]
                self.previousWords[word] = {"url": url, "deleteHash": deleteHash}
                
            previousWordsFile.close()

        self.imgur = Imgur(self.imgurAPIKey)
            
    def llamaItUp(self, word):
        word = re.sub(r"[^A-Za-z\!\?\. ]", '', word).lower()
        
        if word in self.previousWords:
            return self.previousWords[word]["url"]
        else:
            llamaImage = self.llama.new(word)
            imageInfo = self.imgur.upload(llamaImage, word)
            self.storeWord(word, imageInfo)
            return imageInfo["upload"]["links"]["original"]
        
    def storeWord(self, word, imageInfo):
        if not word in self.previousWords:
            self.previousWords[word] = {
                                        "url": imageInfo["upload"]["links"]["original"],
                                        "deleteHash": imageInfo["upload"]["image"]["deletehash"]
                                        }
        
            previousWordsFile = open(self.wordsFileName, 'a')
            previousWordsFile.write("%s;%s;%s\n" % (word, imageInfo["upload"]["links"]["original"],
                                    imageInfo["upload"]["image"]["deletehash"]))
            previousWordsFile.close()


class LlamaText():
    def __init__(self):
        self.letterHeight = 90        
        baseImage = Image.open("plugins/llamas/letterSprites.png")

        self.characters = {
            "a" : baseImage.crop((0, 0, 63, 90)),
            "b" : baseImage.crop((97, 0, 143, 90)),
            "c" : baseImage.crop((172, 0, 229, 90)),
            "d" : baseImage.crop((257, 0, 304, 90)),
            "e" : baseImage.crop((332, 0, 384, 90)),
            "f" : baseImage.crop((411, 0, 461, 90)),
            "g" : baseImage.crop((0, 90, 51, 180)),
            "h" : baseImage.crop((94, 90, 153, 180)),
            "i" : baseImage.crop((184, 90, 217, 180)),
            "j" : baseImage.crop((252, 90, 307, 180)),
            "k" : baseImage.crop((338, 90, 381, 180)),
            "l" : baseImage.crop((411, 90, 463, 180)),
            "m" : baseImage.crop((0, 180, 72, 270)),
            "n" : baseImage.crop((90, 180, 161, 270)),
            "o" : baseImage.crop((179, 180, 238, 270)),
            "p" : baseImage.crop((266, 180, 313, 270)),
            "q" : baseImage.crop((333, 180, 396, 270)),
            "r" : baseImage.crop((419, 180, 456, 270)),
            "s" : baseImage.crop((0, 270, 60, 360)),
            "t" : baseImage.crop((89, 270, 152, 360)),
            "u" : baseImage.crop((175, 270, 236, 360)),
            "v" : baseImage.crop((250, 270, 312, 360)),
            "w" : baseImage.crop((328, 270, 395, 360)),
            "x" : baseImage.crop((405, 270, 489, 360)),
            "y" : baseImage.crop((0, 360, 48, 450)),
            "z" : baseImage.crop((94, 360, 159, 450)),
            "." : baseImage.crop((174, 360, 185, 450)),
            "?" : baseImage.crop((193, 360, 216, 450)),
            "!" : baseImage.crop((222, 360, 233, 450)),
            " " : baseImage.crop((250, 360, 310, 450))
        }
        
        
    def new(self, text):
        totalLength = 0
        workingLength = 0
        text = text.lower()
        
        for letter in text:
            if letter in self.characters:
                totalLength += self.characters[letter].size[0]
            
        newImage = Image.new("RGBA", (totalLength, self.letterHeight), "white")
        
        for letter in text:
            if letter in self.characters: 
                newImage.paste(self.characters[letter], (workingLength, 0))
                workingLength += self.characters[letter].size[0]
                
        return newImage
    
