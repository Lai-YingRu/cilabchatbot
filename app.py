from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
import numpy as np
import pandas as pd
from googletrans import Translator
import QA
##聽力測驗  import-----------------------------------------------
import sys
import datetime
import pygsheets
import QA_Bubble
import random

import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

#Channel Access Token
line_bot_api = LineBotApi('mIg76U+23oiAkDahsjUoK7ElbuYXzLDJcGXaEjaJIfZ+mMqOO3BvX+RlQIzx/Zu0Smy8W08i01F38xGDg6r/thlWLwGxRvcgExAucwMag8KPVAkBFfSLUvgcrxQS4HBzOGIBxoo+zRSJhOFoBEtCVQdB04t89/1O/w1cDnyilFU=')
#Channel Secret  
handler = WebhookHandler('bc9f08c9c29eccb41c7b5b8102b55fd7')
#users = np.array(('0','0',0)) #userID,level_P,point

allUser = [] 
##-----------------------------------------------------------------------------------
##-----------------------------------------------------------------------------------
##解謎  初始抓資料＆資料處理
GDriveJSON = 'JSON.json'
GSpreadSheet_P = 'cilab_ChatBot_puzzle'
gc_Q= pygsheets.authorize(service_account_file='JSON.json')
survey_url_P = 'https://docs.google.com/spreadsheets/d/1nVIgWGQJRIQtMtZSv1HxyDb5FvthBNc0duN4Rlra8to/edit#gid=1732714016'
sh_P = gc_Q.open(GSpreadSheet_P)
sh_P.worksheet_by_title('d0').export(filename='d0')
sh_P.worksheet_by_title('r0').export(filename='r0')
sheet_d0 = pd.read_csv('d0.csv') #type: <class 'pandas.core.frame.DataFrame'>
sheet_r0 = pd.read_csv('r0.csv') 

##----------------------------------------------------------------------------------
def getSheet_P(level): 
    global sh_P  
    if(level == 3):
        sh_P.worksheet_by_title('d3').export(filename='d3')
        sh_P.worksheet_by_title('r3').export(filename='r3')
        sheet_d = pd.read_csv('d3.csv')        
        sheet_r = pd.read_csv('r3.csv') 
    elif(level == 2):
        sh_P.worksheet_by_title('d2').export(filename='d2')
        sh_P.worksheet_by_title('r2').export(filename='r2')
        sheet_d = pd.read_csv('d2.csv')
        sheet_r = pd.read_csv('r2.csv')

    else:        
        sh_P.worksheet_by_title('d1').export(filename='d1')
        sh_P.worksheet_by_title('r1').export(filename='r1')
        sheet_d = pd.read_csv('d1.csv')        
        sheet_r = pd.read_csv('r1.csv') 

    return sheet_d, sheet_r

##----------------------------------------------------------------------------------
sheet_type = 'text'
sheet_reply_list = []
level_P = 1
index_P = 0 #第幾題
isInit_P = True
isChangingLevel_P = False
isChooseHelp = False
isStart_P = False
isAsk_P = False
levelsheet_d, levelsheet_r = getSheet_P(level_P)
_id = 0
##----------------------------------------------------------------------------------
class userVar_P():
    def __init__(self,_id):
        self._id = _id
        self.isInit_P = True
        self.isChangingLevel_P = True
        # self.sheet_type = 'text'
        # self.sheet_title = ''
        # self.sheet_text = ''
        #self.sheet_reply_list = []
        self.level_P = 1
        self.index_P = 0 #第幾題
        self.levelsheet_d, self.levelsheet_r = getSheet_P(self.level_P)

class userVar():
    def __init__(self,_id):
        self._id = _id
        #QA
        self.data_Voc, self.data_Reading, self.data_Cloze = getSheetQA(self.level_Q) #預設傳level = 1
        self.sheet_Q = getVoc.editSheet(self.data_Voc)
        self.isVoc = False 
        self.VocQA = []
        #Listen
        self.data_pho, self.data_word, self.data_sen = getSheet(self.level_L)
        self.sheet_L = self.data_pho
        self.isWord = False 
        self.word_list = []
##-----------------------------------------------------------------------------------
# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'
    
##-----------------------------------------------------------------------------------
#處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):  
    global isInit_P,  isAsk_P, isStart_P, _id
    _id = event.source.user_id
    #user = getUser(event.source.user_id)
    #---------------------------------------    
    if(isInit_P == True or event.message.text =='?'):
        smallpuzzle(event,'d00000',sheet_d0)
        #isChangingLevel_P = True
        isInit_P = False
    elif(isStart_P == True):
        if(isAsk_P == False):
            isAsk_P = True
            LoadQuestion(event)
   
##-----------------------------------------------------------------------------------
def getUser(user_ID):
    global allUser
    user = next((item for item in allUser if item._id == user_ID), None)
    if user is None:
        user = userVar_P(user_ID)
        allUser.append(user)
        print("Alluser",allUser)
    return user 

#回饋判斷
@handler.add(PostbackEvent)
def handle_postback(event):
    global isChooseHelp, level_P, isChangingLevel_P,_id
    #_id = getUser(event.source.user_id)
    pb_event = event.postback.data
    print("postbackData = ",pb_event )

    if pb_event == 0:
        pass
    #--Game State-----------------------------------
    elif pb_event == '1':
        if isChooseHelp == True:
            isChooseHelp = False
            #了解背景故事
            smallpuzzle(event,'d00100',sheet_d0)
            #重複詢問可以幫您什麼？
            smallpuzzle(event,'d00003',sheet_d0)
    elif pb_event == '2':
        if isChooseHelp == True:
            isChooseHelp = False
            #開始遊戲
            smallpuzzle(event,'d00200',sheet_d0)

    elif pb_event == '3':
        if isChooseHelp == True:
            #結束遊戲
            print("End!")
        pass

    if isChangingLevel_P == True:
        print("-----Set Level-----")
        isChangingLevel_P = False
        print("level = ",int(pb_event))
        #隨機取得題型
        RandomTest()
        level_P = int(pb_event)
        setLevelStory(pb_event)

        
##-----------------------------------------------------------------------------------
def smallpuzzle(event,id, sheet):
    global isChangingLevel_P, isChooseHelp
    print("-------------------")
    # id_three = id[3]
    next_id = id[0:3]+ str( int(id[3:6]) + 1).zfill(3)
    print("next id = ", next_id)

    try:
        id_index = sheet["a-descriptionID"].index[sheet["a-descriptionID"] == id]  
        id_index = id_index[0]
        print("id_index",id_index)

        sheet_type = sheet["type"][id_index]
        print("sheet_type",sheet_type)
        

        if sheet_type == 'image':   
            sheet_text = sheet["text"][id_index]  
            print("img= ",sheet_text)                   
            smallpuzzle(event, next_id , sheet)

        elif sheet_type == 'text':
            sheet_text = sheet["text"][id_index]
            print("text= ",sheet_text)
            message = TextSendMessage(text=sheet_text)
            line_bot_api.push_message(_id, message)
       
            smallpuzzle(event, next_id , sheet)

        elif sheet_type == 'button': 
            if id == 'd00003':
                isChooseHelp = True
            elif id == 'd00201':
                isChangingLevel_P = True
            sheet_title = sheet["title"][id_index]
            sheet_text = sheet["text"][id_index]
            sheet_reply_list = []
            for i in range (3):
                if (str(sheet.iloc[id_index][4 + i]) != "") : 
                    sheet_reply_list.append((str(sheet.iloc[id_index][4 + i])))

            replylist = ButtonPuzzle(sheet_reply_list, sheet_title)
            button_bubble = ButtonBubble(sheet_title, sheet_text, replylist)
            line_bot_api.push_message(_id, button_bubble)  
            #Postback(str(button_bubble))
        
        elif sheet_type == 'confirm':
            CofirmPuzzle(event,sheet,next_id)


    except:
        # if next_id == 'd00209': #選題目階級
        #     Postback('L')
        #elif index == 'd10029': 
        pass

def ButtonPuzzle(sheet_reply_list, title):
    replylist = []
    print("ButtonPuzzle",sheet_reply_list)
    for i in range(len(sheet_reply_list)):
        id_index = sheet_r0["a-replyID"].index[sheet_r0["a-replyID"] == sheet_reply_list[i]]
        replylist.append(([sheet_r0["label"][id_index[0]], sheet_r0["text"][id_index[0]], sheet_r0["data"][id_index[0]]]))
    print("replylist",replylist) 
    return replylist

def CofirmPuzzle(event,sheet,next_id):
    print("CofirmBubble")
    smallpuzzle(event, next_id , sheet)

def setLevelStory(event):
    print("setLevelStory")
    global levelsheet_d, levelsheet_r, isStart_P
    levelsheet_d, levelsheet_r = getSheet_P(level_P)
    smallpuzzle(event,'d00202',sheet_d0)

    if level_P == 1:
        smallpuzzle(event,'d10000' , levelsheet_d)

    elif level_P == 2:
        smallpuzzle(event,'d20000' , levelsheet_d)

    elif level_P == 3:
        smallpuzzle(event,'d30000' , levelsheet_d)

    isStart_P = True

def RandomTest():
    global test_type_list
    test_type_list = [random.randint(1,7) for _ in range(10)]
    print("*** 10 quiz type = ",test_type_list)

def LoadQuestion(event):
    print("LoadQuestion", index_P)
    test_type = test_type_list[index_P]
    print("test_type = ", test_type)
    #題數引文
    if level_P == 1 :
        test_pretext = "（第$" + str(index_P+1) + "count 題）\n【Silas】：\n勇者$username ，現在是 "+ str(8+index_P) +":00，Ariel 希望我們在傍晚18:00前完成。"
        print(test_pretext)
        message = TextSendMessage(text=test_pretext)
        line_bot_api.push_message(_id, message)
    
    
    elif level_P == 2:
        test_pretext = "（第$" + str(index_P+1) + "count 題）\n【Keith】：\n勇者$username ，現在是 "+ str(8+index_P) +":00，Faun 希望我們在傍晚18:00前完成。"
        print(test_pretext)
        message = TextSendMessage(text=test_pretext)
        line_bot_api.push_message(_id, message)

    elif level_P == 3:
        test_pretext = "（第$" + str(index_P+1) + "【Cynthia】：\n真是太好了！剛好每天晚上Helena都會在他的閣樓唱歌給大家聽，我們趕緊去找，18:00拿去給領主吧！\n勇者，Let's go！"
        print(test_pretext)
        message = TextSendMessage(text=test_pretext)
        line_bot_api.push_message(_id, message)

    #題前故事
    print('--TestPreStory--'+'d'+ str(level_P) + str(test_type) + '000')
    smallpuzzle(event, 'd' + str(level_P) + str(test_type) + '000', levelsheet_d)

def Question_P(event):
    if test_type_list[index_P] == 1:
        print("sheet_pho")
        smallpuzzle(event,'d'+ str(level_P) +'1000',levelsheet_d)
        print("題目")

    elif test_type_list[index_P] == 2:
        print("sheet_word")
        smallpuzzle(event,'d'+ str(level_P) +'2000',levelsheet_d)
        print("題目")

    elif test_type_list[index_P] == 3:
        print("sheet_sen")
        smallpuzzle(event,'d'+ str(level_P) +'3000',levelsheet_d)
        print("題目")

    elif test_type_list[index_P] == 4:
        print("sheet_spexking_word")
        smallpuzzle(event,'d'+ str(level_P) +'4000',levelsheet_d)
        print("題目")

    elif test_type_list[index_P] == 5:
        print("sheet_spexking_sen")
        smallpuzzle(event,'d'+ str(level_P) +'5000',levelsheet_d)
        print("題目")

    elif test_type_list[index_P] == 6:
        print("sheet_cloze")
        smallpuzzle(event,'d'+ str(level_P) +'6000',levelsheet_d)
        print("題目")

    elif test_type_list[index_P] == 7:
        print("sheet_reading")
        smallpuzzle(event,'d'+ str(level_P) +'7000',levelsheet_d)
        print("題目")



def ButtonBubble(sheet_title, sheet_text, replylist):
    level_template = TemplateSendMessage (
                    alt_text = 'Buttons Template',
                    template = ButtonsTemplate (
                        title = sheet_title,
                        text = sheet_text,
                        actions = [
                                PostbackTemplateAction(
                                    label = replylist[0][0], 
                                    text = replylist[0][1],
                                    data = replylist[0][2]
                                ),
                                PostbackTemplateAction(
                                    label = replylist[1][0], 
                                    text = replylist[1][1],
                                    data = replylist[1][2]
                                ),
                                PostbackTemplateAction(
                                    label = replylist[2][0], 
                                    text = replylist[2][1],
                                    data = replylist[2][2]
                                )
                        ]
                    )
                )
    return level_template


##  End------------------------------------------------

import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)