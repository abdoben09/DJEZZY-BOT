import telebot
import requests
import json
import os
from datetime import datetime, timedelta

TOKEN = '7666412332:AAHHgY967tTuQBOyKWI3u-w8pnromJ50AQQ'
ADMIN_ID = '6324866336'
bot = telebot.TeleBot(TOKEN)

REQUIRED_CHANNELS = [
    {'id': '-1002694893131', 'name': 'القناة الأولى 📢', 'url': 'https://t.me/d0k_83'}
]

data_file_path = 'djezzy_data.json'
otp_state_file = 'otp_state.json'

def load_user_data():
    if os.path.exists(data_file_path):
        with open(data_file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

def save_user_data(data):
    with open(data_file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def load_otp_state():
    if os.path.exists(otp_state_file):
        with open(otp_state_file, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

def save_otp_state(data):
    with open(otp_state_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

user_otp_inputs = load_otp_state()

def hide_phone_number(phone_number):
    return phone_number[:4] + '*******' + phone_number[-2:]

def check_subscription(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(channel['id'], user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True

def send_otp(msisdn):
    url = 'https://apim.djezzy.dz/oauth2/registration'
    payload = f'msisdn={msisdn}&client_id=6E6CwTkp8H1CyQxraPmcEJPQ7xka&scope=smsotp'
    headers = {
        'User-Agent': 'Djezzy/2.6.7',
        'Connection': 'close',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cache-Control': 'no-cache'
    }
    try:
        response = requests.post(url, data=payload, headers=headers)
        if response.status_code == 200:
            return True
    except:
        pass
    return False

def verify_otp(msisdn, otp):
    url = 'https://apim.djezzy.dz/oauth2/token'
    payload = f'otp={otp}&mobileNumber={msisdn}&scope=openid&client_id=6E6CwTkp8H1CyQxraPmcEJPQ7xka&client_secret=MVpXHW_ImuMsxKIwrJpoVVMHjRsa&grant_type=mobile'
    headers = {
        'User-Agent': 'Djezzy/2.6.7',
        'Connection': 'close',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cache-Control': 'no-cache'
    }
    try:
        response = requests.post(url, data=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def apply_gift(chat_id, msisdn, access_token, username, name):
    user_data = load_user_data()
    last_applied = user_data.get(str(chat_id), {}).get('last_applied')
    if last_applied:
        last_applied_time = datetime.fromisoformat(last_applied)
        if datetime.now() - last_applied_time < timedelta(days=1):
            bot.send_message(chat_id, "⚠️ لا يمكنك استخدام الهدية الآن. الرجاء الانتظار 24 ساعة كاملة قبل المحاولة مرة أخرى.")
            return False

    url = f'https://apim.djezzy.dz/djezzy-api/api/v1/subscribers/{msisdn}/subscription-product'
    gift_code = 'GIFTWALKWIN2GO'
    payload = {
        'data': {
            'id': 'GIFTWALKWIN',
            'type': 'products',
            'meta': {
                'services': {
                    'steps': 10000,
                    'code': gift_code,
                    'id': 'WALKWIN'
                }
            }
        }
    }
    headers = {
        'User-Agent': 'Djezzy/2.6.7',
        'Connection': 'Keep-Alive',
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': f'Bearer {access_token}'
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        if response_data.get('message') and gift_code in response_data['message']:
            hidden_phone = hide_phone_number(msisdn)
            bot.send_message(
                chat_id,
                f"🎉 تم تفعيل 2G بنجاح!\n\n"
                f"👤 الاسم: {name}\n"
                f"🧑‍💻 اسم المستخدم: @{username}\n"
                f"📞 الرقم: {hidden_phone}"
            )
            user_data[str(chat_id)]['last_applied'] = datetime.now().isoformat()
            save_user_data(user_data)
            return True
    except:
        pass
    bot.send_message(chat_id, "❌ حدث خطأ أثناء عملية التفعيل. يرجى المحاولة لاحقًا.")
    return False

def get_otp_keyboard(current=''):
    buttons = [
        ['1️⃣', '2️⃣', '3️⃣'],
        ['4️⃣', '5️⃣', '6️⃣'],
        ['7️⃣', '8️⃣', '9️⃣'],
        ['❌', '0️⃣', '🔙']
    ]
    markup = telebot.types.InlineKeyboardMarkup()
    for row in buttons:
        btns = [telebot.types.InlineKeyboardButton(text=btn, callback_data=f'otp_{btn[0]}_{current}') for btn in row]
        markup.row(*btns)
    markup.row(telebot.types.InlineKeyboardButton(text='✅ تأكيد الرمز', callback_data=f'otp_confirm_{current}'))
    return markup

@bot.message_handler(commands=['start'])
def handle_start(msg):
    chat_id = msg.chat.id
    if not check_subscription(chat_id):
        markup = telebot.types.InlineKeyboardMarkup()
        for channel in REQUIRED_CHANNELS:
            markup.add(telebot.types.InlineKeyboardButton(text=f"انضم إلى {channel['name']}", url=channel['url']))
        markup.add(telebot.types.InlineKeyboardButton(text='🔎 تحقق من الاشتراك', callback_data='check_subscription'))
        bot.send_message(chat_id, "📢 يجب الاشتراك في القناة التالية أولاً:", reply_markup=markup)
        return
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text='📱 إرسال رقم الهاتف 📱', callback_data='send_number'))
    bot.send_message(chat_id, '• مرحبًا بك 👋\n\n• يمكنك تفعيل 2G الأسبوعية على شريحة جيزي 📶\n\nملاحظة ⚠️: بعد تسجيل رقمك، يجب الانتظار 30 دقيقة قبل التفعيل 🚀', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'check_subscription')
def handle_check_subscription(call):
    chat_id = call.message.chat.id
    if check_subscription(chat_id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(text='📱 إرسال رقم الهاتف 📱', callback_data='send_number'))
        bot.send_message(chat_id, '✅ تم التحقق من اشتراكك في القناة بنجاح!', reply_markup=markup)
    else:
        bot.answer_callback_query(call.id, "❌ لا تزال غير مشترك!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == 'send_number')
def handle_send_number(callback_query):
    chat_id = callback_query.message.chat.id
    bot.send_message(chat_id, 'يرجى إدخال رقم هاتفك الذي يبدأ بـ 07')
    bot.register_next_step_handler_by_chat_id(chat_id, handle_phone_number)

def handle_phone_number(msg):
    chat_id = msg.chat.id
    text = msg.text
    if text.startswith('07') and len(text) == 10:
        msisdn = '213' + text[1:]
        if send_otp(msisdn):
            user_otp_inputs[str(chat_id)] = {'msisdn': msisdn, 'otp': '', 'timestamp': datetime.now().isoformat()}
            save_otp_state(user_otp_inputs)
            bot.send_message(chat_id, '🔢 أدخل رمز OTP الذي استلمته:\n\n▫️ ▫️ ▫️ ▫️ ▫️ ▫️', reply_markup=get_otp_keyboard())
        else:
            bot.send_message(chat_id, '⚠️ فشل في إرسال رمز OTP. حاول مرة أخرى.')
    else:
        bot.send_message(chat_id, '⚠️ رقم غير صالح. تأكد أن الرقم يبدأ بـ 07 ويتكوّن من 10 أرقام.')

def get_otp_display(otp):
    display = ['▫️'] * 6
    for i in range(len(otp)):
        display[i] = otp[i]
    return ' '.join(display)

@bot.callback_query_handler(func=lambda call: call.data.startswith('otp_'))
def handle_otp_buttons(call):
    chat_id = str(call.message.chat.id)
    data = call.data.split('_')
    action = data[1]
    current = ''.join(data[2:]) if len(data) > 2 else ''

    if chat_id not in user_otp_inputs:
        bot.answer_callback_query(call.id, "❌ انتهت الجلسة، يرجى البدء من جديد باستخدام /start", show_alert=True)
        return

    otp_time = datetime.fromisoformat(user_otp_inputs[chat_id]['timestamp'])
    if datetime.now() - otp_time > timedelta(minutes=5):
        bot.answer_callback_query(call.id, "❌ انتهت صلاحية الرمز، يرجى طلب رمز جديد", show_alert=True)
        del user_otp_inputs[chat_id]
        save_otp_state(user_otp_inputs)
        return

    if action == 'confirm':
        if len(current) == 6:
            try:
                bot.edit_message_text(
                    chat_id=int(chat_id),
                    message_id=call.message.message_id,
                    text="⏳ جاري التحقق من الرمز..."
                )
            except:
                pass
            
            tokens = verify_otp(user_otp_inputs[chat_id]['msisdn'], current)
            if tokens:
                user_data = load_user_data()
                user_data[chat_id] = {
                    'username': call.from_user.username,
                    'telegram_id': int(chat_id),
                    'msisdn': user_otp_inputs[chat_id]['msisdn'],
                    'access_token': tokens['access_token'],
                    'refresh_token': tokens['refresh_token'],
                    'last_applied': None
                }
                save_user_data(user_data)
                markup = telebot.types.InlineKeyboardMarkup()
                markup.add(telebot.types.InlineKeyboardButton(text='🎁 تفعيل', callback_data='walkwingift'))
                bot.send_message(int(chat_id), '✅ تم التحقق بنجاح!\n\n⏳ انتظر 30 دقيقة، ثم اضغط على (تفعيل) 🎁', reply_markup=markup)
                del user_otp_inputs[chat_id]
                save_otp_state(user_otp_inputs)
            else:
                bot.send_message(int(chat_id), '❌ الرمز غير صحيح. يرجى المحاولة مرة أخرى.')
        else:
            bot.answer_callback_query(call.id, "❌ يجب أن يتكون الرمز من 6 أرقام!", show_alert=True)
        return

    otp = current
    if action == '❌':
        otp = ''
    elif action == '🔙':
        otp = otp[:-1] if otp else ''
    elif action.isdigit() and len(otp) < 6:
        otp += action

    if otp == current:
        bot.answer_callback_query(call.id)
        return

    user_otp_inputs[chat_id]['otp'] = otp
    save_otp_state(user_otp_inputs)

    display = get_otp_display(otp)
    try:
        bot.edit_message_text(
            chat_id=int(chat_id),
            message_id=call.message.message_id,
            text=f'🔢 أدخل رمز OTP الذي استلمته:\n\n{display}',
            reply_markup=get_otp_keyboard(otp)
        )
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" not in str(e):
            raise e

@bot.callback_query_handler(func=lambda call: call.data == 'walkwingift')
def handle_walkwingift(callback_query):
    chat_id = callback_query.message.chat.id
    user_data = load_user_data()
    if str(chat_id) in user_data:
        user = user_data[str(chat_id)]
        apply_gift(chat_id, user['msisdn'], user['access_token'], user['username'], callback_query.from_user.first_name)

print('✅ البوت شغّال...')
bot.polling()
