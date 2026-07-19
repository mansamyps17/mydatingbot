import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import database
from flask import Flask
import threading

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

database.init_db()

user_steps = {}
current_viewing = {}

# ================= ម៉ឺនុយប៊ូតុងផ្សេងៗ =================
def get_action_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    markup.add(
        KeyboardButton('❤️'), KeyboardButton('💌'), KeyboardButton('👎'), KeyboardButton('💤')
    )
    return markup

def get_profile_menu_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    markup.add(
        KeyboardButton('1 🚀'), KeyboardButton('2'), KeyboardButton('3'), KeyboardButton('4'), KeyboardButton('5')
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 
        "សួស្តី! នេះជា Bot ស្វែងរកមិត្តភក្តិ និងគូស្នេហ៍។\nសូមវាយពាក្យ /myprofile ដើម្បីបង្កើតប្រវត្តិរូបរបស់អ្នកជាមុនសិន។",
        reply_markup=ReplyKeyboardRemove()
    )

# ================= មុខងារគ្រប់គ្រង Profile =================
@bot.message_handler(commands=['myprofile'])
def show_my_profile(message):
    user_id = message.chat.id
    user = database.get_user_by_id(user_id)
    
    if user:
        gender, name, age, bio, photo_id = user
        bot.send_message(user_id, "នេះជាអ្វីដែលប្រវត្តិរូបរបស់អ្នកមើលទៅ៖", reply_markup=ReplyKeyboardRemove())
        bot.send_photo(user_id, photo_id, caption=f"{gender}\n{name}, {age}, {bio}")
        
        menu_text = "1. ស្វែងរកបន្ត 🚀\n2. បំពេញប្រវត្តិរូបម្តងទៀត។\n3. ផ្លាស់ប្តូររូបថត / វីដេអូ។\n4. ផ្លាស់ប្តូរអត្ថបទនៃប្រវត្តិរូប។\n5. បើក Premium ⭐️"
        bot.send_message(user_id, menu_text, reply_markup=get_profile_menu_keyboard())
    else:
        start_registration(message)

@bot.message_handler(func=lambda message: message.text in ['1 🚀', '2', '3', '4', '5'])
def handle_profile_menu(message):
    action = message.text
    chat_id = message.chat.id
    user = database.get_user_by_id(chat_id)
    
    if not user:
        return
        
    if action == '1 🚀':
        bot.send_message(chat_id, "ចាប់ផ្តើមស្វែងរក... 🚀", reply_markup=ReplyKeyboardRemove())
        show_next_profile(chat_id)
        
    elif action == '2':
        start_registration(message)
        
    elif action == '3':
        msg = bot.send_message(chat_id, "សូមផ្ញើរូបថតថ្មីរបស់អ្នកមកកាន់ខ្ញុំ 📸", reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, update_photo_only)
        
    elif action == '4':
        msg = bot.send_message(chat_id, "សូមសរសេរចំណាប់អារម្មណ៍ ឬទីតាំងថ្មីរបស់អ្នក (Bio):", reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, update_bio_only)
        
    elif action == '5':
        bot.send_message(chat_id, "មុខងារ Premium កំពុងស្ថិតក្នុងការអភិវឌ្ឍន៍ 🛠")

def update_photo_only(message):
    if not message.photo:
        msg = bot.send_message(message.chat.id, "សូមផ្ញើជារូបភាព 📸")
        bot.register_next_step_handler(msg, update_photo_only)
        return
    
    new_photo_id = message.photo[-1].file_id
    user = database.get_user_by_id(message.chat.id)
    if user:
        gender, name, age, bio, old_photo = user
        database.add_user(message.chat.id, gender, name, age, bio, new_photo_id)
        bot.send_message(message.chat.id, "✅ រូបថតរបស់អ្នកត្រូវបានផ្លាស់ប្តូរដោយជោគជ័យ!")
        show_my_profile(message)

def update_bio_only(message):
    new_bio = message.text
    user = database.get_user_by_id(message.chat.id)
    if user:
        gender, name, age, old_bio, photo = user
        database.add_user(message.chat.id, gender, name, age, new_bio, photo)
        bot.send_message(message.chat.id, "✅ អត្ថបទប្រវត្តិរូបត្រូវបានផ្លាស់ប្តូរដោយជោគជ័យ!")
        show_my_profile(message)

# ================= វគ្គចុះឈ្មោះ (Registration Flow) =================
def start_registration(message):
    user_steps[message.chat.id] = {} 
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton('ប្រុស 👨'), KeyboardButton('ស្រី 👩'))
    
    msg = bot.send_message(message.chat.id, "១. តើអ្នកជាភេទអ្វី?", reply_markup=markup)
    bot.register_next_step_handler(msg, process_gender_step)

def process_gender_step(message):
    if message.text not in ['ប្រុស 👨', 'ស្រី 👩']:
        msg = bot.send_message(message.chat.id, "សូមជ្រើសរើសភេទដោយប្រើប៊ូតុងខាងក្រោម៖")
        bot.register_next_step_handler(msg, process_gender_step)
        return
        
    user_steps[message.chat.id]['gender'] = message.text
    msg = bot.send_message(message.chat.id, "២. តើអ្នកឈ្មោះអ្វី?", reply_markup=ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_name_step)

def process_name_step(message):
    user_steps[message.chat.id]['name'] = message.text
    msg = bot.send_message(message.chat.id, "៣. តើអ្នកអាយុប៉ុន្មាន?")
    bot.register_next_step_handler(msg, process_age_step)

def process_age_step(message):
    if not message.text.isdigit():
        msg = bot.send_message(message.chat.id, "សូមបញ្ចូលជាតួលេខ។ តើអ្នកអាយុប៉ុន្មាន?")
        bot.register_next_step_handler(msg, process_age_step)
        return
    user_steps[message.chat.id]['age'] = int(message.text)
    msg = bot.send_message(message.chat.id, "៤. សូមសរសេរចំណាប់អារម្មណ៍ ឬទីតាំងរបស់អ្នក (Bio):")
    bot.register_next_step_handler(msg, process_bio_step)

def process_bio_step(message):
    user_steps[message.chat.id]['bio'] = message.text
    msg = bot.send_message(message.chat.id, "៥. ចុងក្រោយ! សូមផ្ញើរូបថតរបស់អ្នកមួយសន្លឹកមកកាន់ខ្ញុំ 📸")
    bot.register_next_step_handler(msg, process_photo_step)

def process_photo_step(message):
    if not message.photo:
        msg = bot.send_message(message.chat.id, "នេះមិនមែនជារូបភាពទេ។ សូមផ្ញើរូបថត 📸")
        bot.register_next_step_handler(msg, process_photo_step)
        return

    photo_id = message.photo[-1].file_id
    data = user_steps[message.chat.id]
    database.add_user(message.chat.id, data['gender'], data['name'], data['age'], data['bio'], photo_id)
    
    bot.send_message(
        message.chat.id, 
        "✅ ប្រវត្តិរូបរបស់អ្នកត្រូវបានបង្កើតដោយជោគជ័យ!\nសូមវាយ /search ដើម្បីចាប់ផ្តើម។"
    )
    show_my_profile(message)

# ================= វគ្គស្វែងរក និងចុច Like/Message =================
@bot.message_handler(commands=['search'])
def search_people(message):
    show_next_profile(message.chat.id)

def show_next_profile(chat_id):
    current_user = database.get_user_by_id(chat_id)
    if not current_user:
        bot.send_message(chat_id, "សូមវាយ /myprofile ដើម្បីចុះឈ្មោះសិន។", reply_markup=ReplyKeyboardRemove())
        return
        
    current_gender = current_user[0] 
    
    user = database.get_random_user(chat_id, current_gender)
    if user:
        other_user_id, other_gender, name, age, bio, photo_id = user 
        current_viewing[chat_id] = other_user_id
        
        caption_text = f"{name}, {age}, {bio}"
        bot.send_photo(chat_id, photo_id, caption=caption_text, reply_markup=get_action_keyboard())
    else:
        target_gender_text = 'នារី' if current_gender == 'ប្រុស 👨' else 'បុរស'
        bot.send_message(
            chat_id, 
            f"សុំទោស មិនទាន់មានអ្នកប្រើប្រាស់ជា{target_gender_text}ផ្សេងទៀតទេនៅពេលនេះ។ សូមរង់ចាំ! 😅", 
            reply_markup=ReplyKeyboardRemove()
        )

@bot.message_handler(func=lambda message: message.text in ['❤️', '💌', '👎', '💤'])
def handle_action(message):
    action = message.text
    chat_id = message.chat.id
    
    if chat_id not in current_viewing:
        bot.send_message(chat_id, "សូមវាយពាក្យ /search ដើម្បីចាប់ផ្តើមសិន។")
        return
        
    viewed_user_id = current_viewing[chat_id]
    
    if action == '❤️':
        bot.send_message(chat_id, "✅ សំណើត្រូវបានបញ្ជូនរង់ចាំការឆ្លើយតប!")
        sender_profile = database.get_user_by_id(chat_id)
        if sender_profile:
            sender_gender, sender_name, sender_age, sender_bio, sender_photo = sender_profile
            caption_text = f"មានអ្នកកំពុងចាប់អារម្មណ៍អ្នក! ❤️\n\n{sender_name}, {sender_age}, {sender_bio}"
            decision_markup = InlineKeyboardMarkup()
            decision_markup.row(
                InlineKeyboardButton('✅ ទទួល', callback_data=f"accept_{chat_id}"),
                InlineKeyboardButton('❌ បដិសេធ', callback_data=f"reject_{chat_id}")
            )
            try: bot.send_photo(viewed_user_id, sender_photo, caption=caption_text, reply_markup=decision_markup)
            except: pass
        show_next_profile(chat_id)

    elif action == '💌':
        msg = bot.send_message(chat_id, "✍️ សូមសរសេរសារដែលអ្នកចង់ផ្ញើទៅកាន់គាត់៖", reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_custom_message, viewed_user_id)
        
    elif action == '👎':
        show_next_profile(chat_id) 
        
    elif action == '💤':
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton('🔍 បន្តស្វែងរក'))
        bot.send_message(chat_id, "អ្នកបានផ្អាកការស្វែងរក។", reply_markup=markup)
        current_viewing.pop(chat_id, None)

def process_custom_message(message, viewed_user_id):
    custom_text = message.text
    chat_id = message.chat.id
    bot.send_message(chat_id, "✅ សារនិងសំណើរបស់អ្នកត្រូវបានបញ្ជូនទៅកាន់គាត់ហើយ!")
    
    sender_profile = database.get_user_by_id(chat_id)
    if sender_profile:
        sender_gender, sender_name, sender_age, sender_bio, sender_photo = sender_profile
        caption_text = f"💌 គាត់មានសារផ្ញើមកអ្នក៖\n« {custom_text} »\n\n{sender_name}, {sender_age}, {sender_bio}"
        decision_markup = InlineKeyboardMarkup()
        decision_markup.row(
            InlineKeyboardButton('✅ ទទួល', callback_data=f"accept_{chat_id}"),
            InlineKeyboardButton('❌ បដិសេធ', callback_data=f"reject_{chat_id}")
        )
        try: bot.send_photo(viewed_user_id, sender_photo, caption=caption_text, reply_markup=decision_markup)
        except Exception as e: print(f"Error: {e}")
            
    show_next_profile(chat_id)

# ================= វគ្គសម្រេចចិត្ត (ទទួល / បដិសេធ) =================
@bot.callback_query_handler(func=lambda call: call.data.startswith('accept_') or call.data.startswith('reject_'))
def handle_match_decision(call):
    action, liker_id = call.data.split('_')
    receiver_id = call.message.chat.id 
    
    if action == 'accept':
        bot.edit_message_caption(caption="✅ អ្នកបានព្រមទទួលសំណើនេះ! អ្នកអាចឆាតទៅគាត់បាន។", chat_id=receiver_id, message_id=call.message.message_id)
        bot.send_message(receiver_id, f"ចុចទីនេះដើម្បីឆាតជាមួយគាត់៖ [ចុចទីនេះ](tg://user?id={liker_id})", parse_mode="Markdown")
        try: bot.send_message(liker_id, f"🎉 អបអរសាទរ! មានអ្នកព្រមទទួលសំណើរបស់អ្នកហើយ!\nចុចទីនេះដើម្បីឆាត៖ [ចុចទីនេះ](tg://user?id={receiver_id})", parse_mode="Markdown")
        except: pass
    elif action == 'reject':
        bot.edit_message_caption(caption="❌ អ្នកបានបដិសេធសំណើនេះ។", chat_id=receiver_id, message_id=call.message.message_id)

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('🔍 បន្តស្វែងរក'))
    bot.send_message(receiver_id, "តើអ្នកចង់បន្តស្វែងរកគូ ឬមិត្តភក្តិទៀតទេ?", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '🔍 បន្តស្វែងរក')
def continue_searching(message):
    show_next_profile(message.chat.id)


# ================= ផ្នែកបន្ថែមសម្រាប់ Web Server (Render & UptimeRobot) =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot កំពុងដំណើរការយ៉ាងរលូន! (Bot is running)"

def run_bot():
    print("Bot ពេលនេះកំពុងដំណើរការ...")
    bot.infinity_polling()

if __name__ == '__main__':
    # បើក Bot ឱ្យដើរនៅក្នុង Background
    threading.Thread(target=run_bot).start()
    
    # បើក Web Server សម្រាប់ UptimeRobot
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)