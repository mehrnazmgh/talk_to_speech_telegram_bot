import requests
from typing import Final
from telegram.ext import Application, CommandHandler 
import telebot
from telebot import types
import time
import sqlite3



     
#response from telegram server
Token: Final = '6924394880:AAEikovwV-m_a4QV-3voXnvQkaZLI-PKDxY'
BOT_USERNAME: Final = 'TSpeech_bot'


bot = telebot.TeleBot(Token)


def send_file(message , chat_id , user_input) :
           # authentication in aipaa's api
           responseAuthorizedAipaaApi = requests.post('https://api.aipaa.ir/auth/token' 
                            
                                                            , data= {
                            # 5KJ6sWa24IbYrXYYvWvmd3GtyJywGFLXTKR85EFK
                            "client_id": "PVUXqySAghrIkLYJu1sovkzpfpVFgJpSbnVorjST",
                            # U5eghdZdiVBrAI7lGolxu1tIE9EcvkKiFBsve8TyFy3wuuJhVJcx1AddGEcyGP49V6lpNuTf8ABGygoWTFHyZ8tjRvhDWcEG0G6UbrrB8fCkRFLbaHi0kF2tPnxiuZ6u
                            "client_secret": "zlKQO5theeWam5c8kDLQ91evNrjiJxoB2XEFS3SdBPUCIq8CgZtLHGEiJNhQfCkwp1IrXmhTelhEfWGq2TJbT7zbBLL2PjQ486o9MqL6K0W4jJkQeV6qVLosoqIQdtQA",
                            "grant_type" : "client_credentials" 
                        } , headers= { 'Content-Type' : 'application/x-www-form-urlencoded'})
           print(responseAuthorizedAipaaApi)

           accessTokenAipaa = responseAuthorizedAipaaApi.json()["access_token"]

                #create a voice tts service
           responseVoiceTtsCreateAipaaApi = requests.post("https://api.aipaa.ir/api/v1/voice/tts/" 
                                                                , data= {
                            "input_text": user_input,
                            "sample_rate": 0 ,
                            "compress" : True 
                        } , headers= { 'Authorization':'bearer '+ accessTokenAipaa })

           getDowloadLinkTtsResponse = responseVoiceTtsCreateAipaaApi.json()["download_link"]
                # print(responseVoiceTtsCreateAipaaApi)

                #api_v1_file_manager_file_download_read
           responseFileManagerFileDownloadRead = requests.get( getDowloadLinkTtsResponse 
                                                                    , headers= { 'Authorization':'bearer '+ accessTokenAipaa } )
           print(responseFileManagerFileDownloadRead)
           with open('./voice.mp3', 'wb') as f:
                    f.write(responseFileManagerFileDownloadRead.content)
                    
                
           bot.send_audio(chat_id=chat_id, audio=open('./voice.mp3', 'rb'))
           time.sleep(5) # Sleep for 5 seconds
           handle_start_help(message)

# ایجاد دکمه های کیبورد
keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.row('/start', '/help')

@bot.message_handler(commands=['/start', '/help'])
def handle_start_help(message):
    sent = bot.send_message(message.chat.id, "لطفا یک گزینه را انتخاب کنید:", reply_markup=keyboard)
    bot.register_next_step_handler(sent, handle_all_messages)
    
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text == '/start':
        start_command(message)
        # print("start")
    elif message.text == '/help':
        help_command(message)
        # print("help")
    else:

        pass

    
#commands
@bot.message_handler(commands=['start'])
def start_command(message):
    sent = bot.send_message(message.chat.id, 'سلام به بات تبدیل متن به صدا خوش آمدید.لطفا پیام خود را ارسال کنید')
    bot.register_next_step_handler(sent, handle_user_input)
    
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, 'این بات برای تبدیل متن به صدا ایجاد شده است.برای این منظور متن دلخواه خود را ارسال کنید و صدای متن را دریافت کنید.')
    time.sleep(3) # Sleep for 3 seconds
    handle_start_help(message)
    
def handle_user_input(message):
    chat_id = message.chat.id
    # print(chat_id)
    user_input = message.text
    # echo_all(message)  

    #create database
    conn = sqlite3.connect('text_to_speech.db')
    
    #create table for user included chat_ids and download_counts
    # conn.execute('''CREATE TABLE users
    #                 (chat_id TEXT PRIMARY KEY     NOT NULL,
    #                 download_count   INT    NOT NULL
    #                 )''')
    
    
    # select the chat_id from users table
    query = conn.execute('''SELECT * from users WHERE chat_id = {0}'''.format(chat_id)) 
    
    table = query.fetchall()
    
    print(table)
    
    #check database update or insert into users table
    if len(table) !=0 :
        
        #check limit for downloads each user has
        if table[0][1] >= 3 :
            bot.send_message(message.chat.id, 'کاربر گرامی محدودیت استفاده از این بات به پایان رسیده است.هر کاربر تنها مجاز به دانلود 3 فایل می باشد.')
            time.sleep(3) # Sleep for 3 seconds
            handle_start_help(message)
                
        else:
            bot.send_message(message.chat.id, "ممنون از پیام شما! فایل صوتی تا لحظاتی دیگر برای شما ارسال می شود.")
            user_chat_id = table[0][0]
            # print(user_chat_id)
            user_download_count = table[0][1] + 1
            # print(user_download_count)
            conn.execute('''UPDATE users SET download_count = {0} WHERE chat_id = {1}'''.format(user_download_count , user_chat_id))
            print('update')
            send_file(message , chat_id , user_input)        
            
    else :
        download_count = 1
        conn.execute('''INSERT INTO users (chat_id, download_count) \
                VALUES (?, ?)''', (chat_id, download_count))
        print('insert')
        send_file(message , chat_id , user_input)
        
    conn.commit()
    conn.close()


bot.polling()
if __name__ == '__main__':
    app = Application.builder().token(Token).build()   
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    
    app.run_polling(poll_interval=3)
    