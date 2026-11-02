# 🚀 PostBot - Advanced Telegram Post Creator Bot

Telegram का सबसे बेहतरीन, Clean और Premium Post Creator Bot — बिल्कुल **@PostBot** जैसा, लेटेस्ट **Telegram Bot API (Color Buttons)**, **Direct Channel Posting** और **All-Format Admin Broadcast** फीचर्स के साथ!

---

## ✨ Features (मुख्य विशेषताएं)

1. **📢 Admin Broadcast System (`/cast`):**
   - सिर्फ बॉट एडमिन ही ब्रॉडकास्ट कर सकता है।
   - **सभी फॉर्मेट्स सपोर्टेड**: 
     - 📝 Text (बोल्ड, इटैलिक, लिंक्स, इमोजी व स्पॉइलर के साथ)
     - 🖼️ Photos
     - 🎥 Videos (बड़ी वीडियोज़ भी)
     - 📁 Documents / Files
     - 🎵 Music / Audio
     - 🎙️ Voice Notes
     - 🎞️ GIFs / Animations
     - 🎭 Stickers
     - 🔘 Posts with Inline Buttons
   - **Live Preview + Confirmation**: भेजने से पहले लाइव प्रीव्यू दिखता है और कन्फर्म करने का बटन आता है।
   - **Real-Time Progress & Stats**: लाइव प्रोग्रेस (जैसे 250/1000 Users) और अंत में पूरी रिपोर्ट (सफलतापूर्वक पहुंचे, ब्लॉक किए गए, कुल समय)।

2. **📢 Direct Channel & Group Posting:**
   - बॉट को 1-क्लिक में एडमिन बनाने का बटन (`➕ Add to Channel`, `👥 Add to Group`)।
   - पोस्ट तैयार होने पर **`🚀 Send to Channel`** बटन दबाकर सीधे किसी भी चैनल में पोस्ट भेजें।

3. **🌐 20 Global Languages:**
   - 🇬🇧 EN, 🇷🇺 RU, 🇺🇿 UZ, 🇰🇿 KZ, 🇦🇿 AZ, 🇹🇷 TR, 🇸🇦 AR, 🇨🇳 ZH, 🇮🇳 HI, 🇪🇸 ES, आदि।

4. **🎨 Color Inline Buttons:**
   - 🟢 Green (`success`), 🔵 Blue (`primary`), 🔴 Red (`danger`), ⚪ No color।

5. **⚡ Super Fast Speed:**
   - SQLite WAL मोड + बैनर File ID कैशिंग। 0 VPS डिस्क स्टोरेज।

---

## 🛠️ Installation & Setup (सेटअप कैसे करें)

### Step 1: Dependencies Install करें
```bash
pip3 install -r requirements.txt
```

### Step 2: `.env` कॉन्फ़िगर करें
```env
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
BOT_USERNAME=YOUR_BOT_USERNAME
DATABASE_PATH=data/postbot.db
ADMIN_IDS=12345678,87654321
```
*(अपनी टेलीग्राम यूजर आईडी `ADMIN_IDS` में डालें ताकि सिर्फ आप `/cast` कमांड चला सकें। Multiple Admins के लिए कॉमा लगा सकते हैं।)*

### Step 3: @BotFather में Inline Mode चालू करें
1. [@BotFather](https://t.me/BotFather) पर जाएं।
2. `/setinline` भेजें।
3. अपने बॉट को सेलेक्ट करें और `Enter post code...` लिखें।

### Step 4: बॉट चलाएं
```bash
python3 main.py
```

---

## 📢 How to Use Broadcast (ब्रॉडकास्ट कैसे चलाएं)
1. बॉट में `/cast` (या `/broadcast`) कमांड भेजें।
2. बॉट कुल रजिस्टर्ड यूज़र्स की संख्या दिखाएगा और कंटेंट मांगेगा।
3. कोई भी फोटो, वीडियो, फाइल, टेक्स्ट या बटनों वाला मैसेज भेजें।
4. बॉट आपको लाइव प्रीव्यू दिखाएगा।
5. `🚀 Confirm & Send` पर क्लिक करते ही सभी यूज़र्स को ब्रॉडकास्ट जाना शुरू हो जाएगा!
