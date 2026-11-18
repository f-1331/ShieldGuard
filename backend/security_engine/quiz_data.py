"""
ShieldGuard AI - Kiber-Savodxonlik va Psixologik Xulq-atvor Test Tizimi.
10 ta daraja (Juda osondan boshlanib murakkablashib boradi), har birida 10 tadan real hayotiy savol (Jami: 100 ta savol).
Odamlarning stress, qiziqish, qo'rquv, ochko'zlik va shoshilish holatlarida o'zini qanday tutishini tahlil qiladi.
"""

import random
from typing import Dict, List, Any, Optional

LEVELS_META = {
    1: {
        "title": "🌱 1-Daraja: Boshlang'ich Kiber-Gigiyena",
        "difficulty": "Juda Oson",
        "badge": "Yangi O'rganuvchi",
        "desc": "Kundalik eng oddiy kiber-qoidalar: SMS kodlar, oddiy parollar, ochiq Wi-Fi va begonalarga telefon bermaslik."
    },
    2: {
        "title": "📱 2-Daraja: Telegram va Ijtimoiy Tarmoqlar",
        "difficulty": "Oson",
        "badge": "Ijtimoiy Himoyachi",
        "desc": "Telegram 'ovoz berish' (golos), tekin Premium tuzoqlari, 2-bosqichli parol (2FA) va soxta kanallar."
    },
    3: {
        "title": "💳 3-Daraja: Bank Kartalari va To'lov Xavfsizligi",
        "difficulty": "O'rta-Oson",
        "badge": "Moliya Posboni",
        "desc": "CVV/CVC kodlar, soxta to'lov cheklari, 'Click/Payme bonus' aksiyalari va karta ma'lumotlarini himoyalash."
    },
    4: {
        "title": "🎣 4-Daraja: Fishing va Soxta Saytlar (Domenlar)",
        "difficulty": "O'rta",
        "badge": "Fishing Ovchisi",
        "desc": "Soxta manzillar (typosquatting), qisqartirilgan xavfli havolalar, soxta login oynalari va SSL qulf aldamchiligi."
    },
    5: {
        "title": "☣️ 5-Daraja: Zararli APK va Android Troyanlar",
        "difficulty": "O'rta-Qiyin",
        "badge": "Antivirus Qalqoni",
        "desc": "'Fotosurat.apk', 'Taklifnoma.apk', noqonuniy Telegram modlar va maxsus imkoniyatlar (Accessibility) tuzoqlari."
    },
    6: {
        "title": "🎭 6-Daraja: Ijtimoiy Muhandislik va Psixologik Bosim",
        "difficulty": "Qiyin",
        "badge": "Ruhiy Barqaror Himoyachi",
        "desc": "Shoshilinch qo'rquv ('Hisobingiz 5 daqiqada muzlaydi!'), soxta tergovchi qo'ng'iroqlari va stress ostida qaror qabul qilish."
    },
    7: {
        "title": "💰 7-Daraja: Soxta Ish, Investitsiya va Kripto Piramidalar",
        "difficulty": "Qiyin",
        "badge": "Moliyaviy Strateg",
        "desc": "'Kuniga 500,000 so'm layk bosib ishlash', soxta treyding botlari va kafolatlangan tekin daromad illyuziyasi."
    },
    8: {
        "title": "🤖 8-Daraja: Deepfake va Sun'iy Intellekt Firibgarligi",
        "difficulty": "Juda Qiyin",
        "badge": "AI-Xavfsizlik Mutaxassisi",
        "desc": "Ovoz klonlash orqali pul so'rash, videoqo'ng'iroqdagi AI niqoblar va soxtalashtirilgan audio dalillar."
    },
    9: {
        "title": "🏢 9-Daraja: Korporativ va Ish Joyidagi Kiber-Hujumlar",
        "difficulty": "Ekspert",
        "badge": "Kiber-Xavfsizlik Ofitseri",
        "desc": "Soxta rahbar xabarlari (CEO Fraud), zararli hisob-fakturalar (invoice.pdf.exe), BadUSB va ma'lumot sizishi."
    },
    10: {
        "title": "⚔️ 10-Daraja: Ekstremal Kiber-Hujumlar va Kiber-Grossmeyster",
        "difficulty": "Grossmeyster (Eng Murakkab)",
        "badge": "Oliy Kiber-Grossmeyster",
        "desc": "SIM-swap, sessiya o'g'irlash (Session Hijack), QR-ishing (Quishing), Man-in-the-Middle va zero-day psixologiyasi."
    }
}

ALL_QUIZ_DATA: Dict[int, List[Dict[str, Any]]] = {
    # -------------------------------------------------------------
    # LEVEL 1: Boshlang'ich Kiber-Gigiyena (10 ta savol)
    # -------------------------------------------------------------
    1: [
        {
            "id": 101,
            "title": "SMS tasdiqlash kodi",
            "scenario": "SMS orqali bankdan 6 xonali tasdiqlash kodi keldi. Notanish kishi qo'ng'iroq qilib adashib sizning raqamingizni kiritganini aytib, kodni so'ramoqda.",
            "question": "Siz ushbu vaziyatda qanday yo'l tutasiz?",
            "behavior_type": "trust_exploit",
            "options": [
                {
                    "text": "Kodni unga aytaman, chunki insoniylik yuzasidan yordam berish kerak.",
                    "is_correct": False,
                    "behavior": "Haddan tashqari ishonuvchan / Xavfni sezmaydigan",
                    "explanation": "❌ Katta xato! Bank SMS kodlari hech qachon birovga berilmaydi. Bu orqali kartangizdagi barcha mablag' bir zumda yechib olinadi."
                },
                {
                    "text": "Kodni aslo aytmayman va qo'ng'iroqni tugataman.",
                    "is_correct": True,
                    "behavior": "Ehtiyotkor va to'g'ri fikrlovchi",
                    "explanation": "✅ To'g'ri! Hech kimga va hech qanday holatda SMS kodni bermaslik — kiber-gigiyenaning 1-oltin qoidasidir."
                },
                {
                    "text": "Kodni noto'g'ri qilib ataylab boshqa raqam aytaman.",
                    "is_correct": False,
                    "behavior": "Tavakkalchi",
                    "explanation": "⚠️ Xavfli! Firibgar bilan dialogga kirishish orqali siz unga qo'shimcha psixologik imkoniyat yaratasiz. Eng to'g'risi — aloqani uzish."
                }
            ]
        },
        {
            "id": 102,
            "title": "Karta pin-kodi",
            "scenario": "Bankomat oldida turgan notanish kishi ko'zi yaxshi ko'rmayotganini aytib, kartangiz PIN-kodini aytib yuborishni va pul yechib berishni iltimos qildi.",
            "question": "O'z kartangiz PIN-kodini unga aytasizmi?",
            "behavior_type": "privacy_risk",
            "options": [
                {
                    "text": "Ha, ko'zi ojiz odamga yordam qilish savob.",
                    "is_correct": False,
                    "behavior": "Soddadil",
                    "explanation": "❌ PIN-kod mutlaqo maxfiy ma'lumot! Uni hech kimga ovoz chiqarib aytish mumkin emas."
                },
                {
                    "text": "Yo'q, PIN-kodimni hech kimga aytmayman, xohlasa xodimni chaqirib beraman.",
                    "is_correct": True,
                    "behavior": "Hushyor himoyachi",
                    "explanation": "✅ To'g'ri! Yordam berish mumkin, lekin shaxsiy maxfiy parollarni hech qachon oshkor qilmaslik sharti bilan."
                },
                {
                    "text": "PIN-kodni aytaman, lekin keyinroq o'zgartirib olaman.",
                    "is_correct": False,
                    "behavior": "Dangasa / E'tiborsiz",
                    "explanation": "❌ Xato! Bir necha daqiqa ichida kartangiz bo'shatilishi yoki klonlanishi mumkin."
                }
            ]
        },
        {
            "id": 103,
            "title": "Ommaviy bepul Wi-Fi",
            "scenario": "Kafeda 'Free_Public_WiFi' ochiq Wi-Fi tarmog'iga ulandingiz. Shunda Payme yoki bank ilovasiga kirib pul o'tkazmoqchisiz.",
            "question": "Ochiq Wi-Fi da bank ilovasidan foydalanish xavfsizmi?",
            "behavior_type": "convenience_trap",
            "options": [
                {
                    "text": "Ha, bepul internet bor ekan, tezda pul o'tkazib olaman.",
                    "is_correct": False,
                    "behavior": "Qulaylikka aldanuvchi",
                    "explanation": "❌ Ochiq Wi-Fi tarmoqlarida firibgarlar parollarni va to'lov ma'lumotlarini osongina ushlab olishi (sniffing) mumkin."
                },
                {
                    "text": "Yo'q, bank ilovasiga faqat shaxsiy mobil internetim orqali kiraman.",
                    "is_correct": True,
                    "behavior": "Xavfsizlikni birinchi o'ringa qo'yuvchi",
                    "explanation": "✅ Barakalla! Moliyaviy operatsiyalar uchun faqat himoyalangan mobil internet (3G/4G/5G) ishlatilishi shart."
                },
                {
                    "text": "Wi-Fi orqali faqat kichikroq summa o'tkazaman.",
                    "is_correct": False,
                    "behavior": "O'zini aldaydigan",
                    "explanation": "❌ Summaning ahamiyati yo'q, hisob login-parolingiz qo'lga kiritilsa butun kartangiz xavf ostida qoladi."
                }
            ]
        },
        {
            "id": 104,
            "title": "Oddiy parollar (123456)",
            "scenario": "Telefoningiz yoki pochtangizga yangi parol o'rnatyapsiz. Qaysi parolni tanlaysiz?",
            "question": "Eng xavfsiz parol qaysi biri?",
            "behavior_type": "laziness_vs_security",
            "options": [
                {
                    "text": "12345678 yoki o'zimning tug'ilgan yilim (masalan 1995)",
                    "is_correct": False,
                    "behavior": "O'ta beparvo",
                    "explanation": "❌ Bunday parollar firibgarlar tomonidan bir necha soniyada avtomatik dasturlar bilan buziladi."
                },
                {
                    "text": "Katta-kichik harflar, raqamlar va maxsus belgilar aralashmasi (masalan: Sh!eld#G92)",
                    "is_correct": True,
                    "behavior": "Kuchli xavfsizlik madaniyatiga ega",
                    "explanation": "✅ To'g'ri! Murakkab va kamida 8-12 belgili parollarni buzish o'ta qiyin."
                },
                {
                    "text": "Ismim va orqasiga 123 qo'yaman (masalan: Sardor123)",
                    "is_correct": False,
                    "behavior": "Yuzaki ehtiyotkor",
                    "explanation": "❌ Ism + raqam kombinatsiyalari eng birinchi lug'at hujumlari (dictionary attack) ro'yxatida turadi."
                }
            ]
        },
        {
            "id": 105,
            "title": "Ko'chada notanishga telefon berish",
            "scenario": "Ko'chada notanish yigit yaqinim kasalxonada, telefonim o'chib qoldi, bitta qo'ng'iroq qilib olay deb iltimos qildi.",
            "question": "O'z telefoningizni uning qo'liga tutqazasizmi?",
            "behavior_type": "empathy_exploit",
            "options": [
                {
                    "text": "Telefonimni ochib qo'liga beraman va chetda kutib turaman.",
                    "is_correct": False,
                    "behavior": "Haddan tashqari ishonuvchan",
                    "explanation": "❌ Firibgar bir zumda qochib ketishi yoki telefoningizdan pul yechuvchi USSD kodni terishi mumkin."
                },
                {
                    "text": "Raqamni o'zim terib, spikerda (karnayda) gaplashishini aytaman, telefonni qo'limda ushlab turaman.",
                    "is_correct": True,
                    "behavior": "Hushyor va oqil ko'makchi",
                    "explanation": "✅ A'lo qaror! Yordam qildingiz, lekin qurilmangiz to'liq o'z nazoratingizda qoldi."
                },
                {
                    "text": "Umuman gaplashmay so'kib haydab yuboraman.",
                    "is_correct": False,
                    "behavior": "Agressiv",
                    "explanation": "⚠️ Insoniylikni saqlagan holda xavfsizlik chorasini ko'rish eng to'g'ri yo'ldir."
                }
            ]
        },
        {
            "id": 106,
            "title": "Ekranni qulflash (Lock Screen)",
            "scenario": "Ishxonada yoki kafeda choy ichish uchun stolingizdan 5 daqiqaga turmoqchisiz. Telefon va noutbuk qulflanmagan.",
            "question": "Nima qilasiz?",
            "behavior_type": "habitual_negligence",
            "options": [
                {
                    "text": "Hech narsa qilmayman, 5 daqiqada nima ham bo'lardi.",
                    "is_correct": False,
                    "behavior": "Beparvo",
                    "explanation": "❌ 5 daqiqa ichida xohlagan odam Telegramingizni o'qishi yoki fayllaringizni fleshkaga ko'chirishi mumkin."
                },
                {
                    "text": "Qurilmalarni darhol qulflayman (Win+L / Ekranni o'chirish).",
                    "is_correct": True,
                    "behavior": "Tartibli kiber-mutaxassis",
                    "explanation": "✅ To'g'ri! Qurilmadan uzoqlashdingizmi — darhol ekran qulflanishi shart."
                },
                {
                    "text": "Ustiga daftar yoki ro'molcha yopib ketaman.",
                    "is_correct": False,
                    "behavior": "Soddadil",
                    "explanation": "❌ Bu hech qanday himoya bermaydi."
                }
            ]
        },
        {
            "id": 107,
            "title": "Barcha joyda bitta parol ishlatish",
            "scenario": "Instagram, Telegram, Gmail va Bank ilovangizga bitta umumiy paroldan foydalanasiz.",
            "question": "Bu xavfsizmi?",
            "behavior_type": "security_shortcut",
            "options": [
                {
                    "text": "Ha, juda qulay, esdan chiqmaydi.",
                    "is_correct": False,
                    "behavior": "Dangasa",
                    "explanation": "❌ Bitta saytdan parolingiz o'g'irlansa, barcha akkauntlaringiz bir kunda boy beriladi!"
                },
                {
                    "text": "Yo'q, har bir muhim xizmat uchun alohida unikal parol bo'lishi kerak.",
                    "is_correct": True,
                    "behavior": "Tizimli fikrlovchi",
                    "explanation": "✅ To'g'ri! Parollar bir xil bo'lmasligi kerak. Eslab qolish uchun Parol menejerlaridan foydalanish tavsiya etiladi."
                },
                {
                    "text": "Faqat oxiriga har xil nuqta qo'yib chiqaman.",
                    "is_correct": False,
                    "behavior": "Yuzaki himoyachi",
                    "explanation": "❌ Bunday o'xshashlikni hakerlar juda tez hisoblab chiqishadi."
                }
            ]
        },
        {
            "id": 108,
            "title": "Telefonga begona USB ulash",
            "scenario": "Metroda yoki avtobusda devordagi bepul USB zaryadka portiga telefoningizni to'g'ridan-to'g'ri kabel bilan uladingiz.",
            "question": "Buning qanday xavfi bor?",
            "behavior_type": "convenience_over_caution",
            "options": [
                {
                    "text": "Hech qanday xavfi yo'q, shunchaki zaryad oladi.",
                    "is_correct": False,
                    "behavior": "Bexabar",
                    "explanation": "❌ 'Juice Jacking' xavfi mavjud — ommaviy USB portlar orqali telefonga troyan yuklanishi mumkin."
                },
                {
                    "text": "Kabel orqali ma'lumotlar o'g'irlanishi mumkin, faqat oddiy 220V adapter yoki Powerbank ishlatish kerak.",
                    "is_correct": True,
                    "behavior": "Texnologik savodxon",
                    "explanation": "✅ To'g'ri! Ommaviy USB portlardan faqat quvvatlagich blok (adapter) orqali yoki o'z Powerbankingizdan quvvatlang."
                },
                {
                    "text": "Faqat 10 foiz zaryad olgunicha ulab tursam xavfsiz.",
                    "is_correct": False,
                    "behavior": "Vaqtga aldanuvchi",
                    "explanation": "❌ Ma'lumot nusxalash bir necha soniyada amalga oshadi."
                }
            ]
        },
        {
            "id": 109,
            "title": "Telegramda fotosurat so'rash",
            "scenario": "Notanish profil sizga: 'Salom, do'st bo'laylik, rasmingizni va pasportingizni yuboring' deb yozdi.",
            "question": "Shaxsiy hujjatlarni notanishlarga yuborasizmi?",
            "behavior_type": "social_naivety",
            "options": [
                {
                    "text": "Ha, yangi do'st orttirish yaxshi narsa.",
                    "is_correct": False,
                    "behavior": "O'ta sodda",
                    "explanation": "❌ Pasport ma'lumotlaringiz nomingizga soxta onlayn kreditlar olishda ishlatiladi!"
                },
                {
                    "text": "Aslo yo'q! Shaxsiy hujjat va rasmlar hech qachon notanishlarga berilmaydi.",
                    "is_correct": True,
                    "behavior": "Qat'iy va himoyalangan",
                    "explanation": "✅ Barakalla! Shaxsiy ma'lumotlar sir saqlanishi kerak."
                },
                {
                    "text": "Faqat pasport raqamini beraman, rasmini yubormayman.",
                    "is_correct": False,
                    "behavior": "Chala ehtiyotkor",
                    "explanation": "❌ Seriya va raqamning o'zi ham firibgarlar uchun yetarli ma'lumotdir."
                }
            ]
        },
        {
            "id": 110,
            "title": "Ilova yangilanishlari (Updates)",
            "scenario": "Telefoningiz operatsion tizimi xavfsizlik yangilanishi (Security Update) kelganini bildirdi.",
            "question": "Siz qanday yo'l tutasiz?",
            "behavior_type": "procrastination",
            "options": [
                {
                    "text": "Yangilanishlarni e'tiborsiz qoldiraman, telefon sekinlashadi deb o'ylayman.",
                    "is_correct": False,
                    "behavior": "Eskicha fikrlovchi",
                    "explanation": "❌ Yangilanmagan dasturlar hakerlar uchun ochiq eshikdir."
                },
                {
                    "text": "Xavfsizlik yangilanishini imkon qadar tezroq o'rnataman.",
                    "is_correct": True,
                    "behavior": "Mas'uliyatli foydalanuvchi",
                    "explanation": "✅ To'g'ri! Yangilanishlar avvalgi xavfsizlik teshiklarini (vulnerabilities) yopadi."
                },
                {
                    "text": "Faqat 1 yildan keyin yangilayman.",
                    "is_correct": False,
                    "behavior": "Dangasa",
                    "explanation": "❌ 1 yil ichida qurilmangiz bir necha bor nishonga olinishi mumkin."
                }
            ]
        }
    ],

    # -------------------------------------------------------------
    # LEVEL 2: Telegram va Ijtimoiy Tarmoqlar (10 ta savol)
    # -------------------------------------------------------------
    2: [
        {
            "id": 201,
            "title": "Telegram Ovoz Berish (Golos) firibgarligi",
            "scenario": "Tanish do'stingizning nomidan xabar keldi: 'Salom, jiyanim bolalar tanlovida qatnashyapti, iltimos mana bu havola orqali ovoz berib yubor'.",
            "question": "Havolani ochsangiz, u sizdan Telegram kodingizni so'rayapti. Nima qilasiz?",
            "behavior_type": "social_manipulation",
            "options": [
                {
                    "text": "Do'stim iltimos qilgani uchun kodni kiritib ovoz beraman.",
                    "is_correct": False,
                    "behavior": "Ko'r-ko'rona ishonuvchan",
                    "explanation": "❌ Eng keng tarqalgan tuzoq! Do'stingizning o'zi akkauntini oldirib qo'ygan. Kodni kiritishingiz bilan profilingiz o'g'irlanadi."
                },
                {
                    "text": "Darhol sahifani yopaman va do'stimga telefon qilib ogohlantiraman.",
                    "is_correct": True,
                    "behavior": "Analitik va hushyor",
                    "explanation": "✅ A'lo! Telegram kodini hech qachon tashqi saytlarga kiritmaslik kerak."
                },
                {
                    "text": "Ovoz berish tugmasini bosaman, lekin kod kiritmay kutaman.",
                    "is_correct": False,
                    "behavior": "Qiziquvchan",
                    "explanation": "⚠️ Shubhali sahifalarni ochishning o'ziyoq xavfli skriptlarni ishga tushirishi mumkin."
                }
            ]
        },
        {
            "id": 202,
            "title": "Telegram 2-Bosqichli Parol (Two-Step Verification)",
            "scenario": "Telegram sozlamalarida 2-bosqichli tasdiqlash (Bulutli parol / Cloud Password) funksiyasi mavjud.",
            "question": "Siz bu funksiyani yoqib qo'yganmisiz?",
            "behavior_type": "security_proactiveness",
            "options": [
                {
                    "text": "Yo'q, ortiqcha boshog'riq, har safar parol so'raydi.",
                    "is_correct": False,
                    "behavior": "Xavfga befarq",
                    "explanation": "❌ 2FA yoqilmagan bo'lsa, firibgar bitta SMS kod orqali profilingizni butunlay tortib oladi."
                },
                {
                    "text": "Ha, murakkab parol va tiklash emaili bilan yoqib qo'yganman.",
                    "is_correct": True,
                    "behavior": "Mukammal himoyalangan",
                    "explanation": "✅ Barakalla! 2FA — Telegram o'g'irlanishining 99% oldini oluvchi eng muhim qalqondir."
                },
                {
                    "text": "Yoqqanman, lekin parolini 1111 qilib qo'yganman.",
                    "is_correct": False,
                    "behavior": "Yuzaki himoyalangan",
                    "explanation": "❌ Oddiy parollarni firibgarlar oson topadi."
                }
            ]
        },
        {
            "id": 203,
            "title": "Tekin Telegram Premium sovg'asi",
            "scenario": "Guruhda bot xabar yubordi: 'Tabriklaymiz! Sizga 1 yillik bepul Telegram Premium berildi. Sovg'ani olish uchun quyidagi botga kiring va start bosing'.",
            "question": "Ushbu botga kirasizmi?",
            "behavior_type": "freebie_greed",
            "options": [
                {
                    "text": "Ha, tekin Premium berilayotgan bo'lsa albatta olaman.",
                    "is_correct": False,
                    "behavior": "Ochko'zlik tuzog'iga tushuvchi",
                    "explanation": "❌ Bepul pishloq faqat qopqonda bo'ladi. Bu bot profilingizni botnetga aylantiradi yoki pulingizni yechadi."
                },
                {
                    "text": "Xabarni firibgarlik deb belgilayman (Report) va botga kirmayman.",
                    "is_correct": True,
                    "behavior": "Oqil va hushyor",
                    "explanation": "✅ To'g'ri! Telegram Premium faqat rasmiy xarid qilinadi yoki haqiqiy do'stlar tomonidan rasmiy sovg'a qilinadi."
                },
                {
                    "text": "Guruhdagi boshqa do'stlarimga ham jo'nataman.",
                    "is_correct": False,
                    "behavior": "Xavf tarqatuvchi",
                    "explanation": "❌ O'zingiz tushgan tuzoqqa yaqinlaringizni ham tortgan bo'lasiz."
                }
            ]
        },
        {
            "id": 204,
            "title": "Telegram Faol Sessiyalar (Active Sessions)",
            "scenario": "Telegramingizda 'Sozlamalar -> Qurilmalar (Devices)' bo'limini qachon oxirgi marta tekshirdingiz?",
            "question": "U yerda notanish qurilma (masalan, Windows yoki Linux) ko'rsangiz nima qilasiz?",
            "behavior_type": "security_audit",
            "options": [
                {
                    "text": "Darhol 'Boshqa barcha seanslarni tugatish' (Terminate all other sessions) tugmasini bosaman va 2FA parolini o'zgartiraman.",
                    "is_correct": True,
                    "behavior": "Tezkor va to'g'ri chora ko'ruvchi",
                    "explanation": "✅ A'lo! Notanish qurilma bo'lsa, demak profilingiz boshqa odam tomonidan o'qilmoqda."
                },
                {
                    "text": "E'tibor bermayman, balki o'zim qachondir kirgandirman.",
                    "is_correct": False,
                    "behavior": "G'aflatda qoluvchi",
                    "explanation": "❌ Xato! Yashirin kuzatuvchilar yillab xabarlaringizni o'qib yurishi mumkin."
                },
                {
                    "text": "Telegramni o'chirib qayta o'rnataman.",
                    "is_correct": False,
                    "behavior": "Chala tushunuvchi",
                    "explanation": "⚠️ Telegramni telefondan o'chirish boshqa qurilmadagi begona sessiyani to'xtatmaydi!"
                }
            ]
        },
        {
            "id": 205,
            "title": "Soxta kanallar va botlar",
            "scenario": "Telegramda 'Payme Rasmiy Kanali' nomli kanal ko'rdingiz. Obunachisi 1000 ta, postlarida esa 'Kartangizni tasdiqlang' deb link berilgan.",
            "question": "Bu haqiqiy rasmiy kanalmi?",
            "behavior_type": "impersonation_detection",
            "options": [
                {
                    "text": "Ha, logotipi va nomi rasmiy ekan, demak to'g'ri.",
                    "is_correct": False,
                    "behavior": "Yuzaki baholovchi",
                    "explanation": "❌ Logotip va nomni xohlagan firibgar 1 daqiqada qo'yib olishi mumkin."
                },
                {
                    "text": "Yo'q, rasmiy kanallarda ko'k tasdiqlangan belgi (verified badge) bo'ladi va ular hech qachon karta tasdiqlashni so'ramaydi.",
                    "is_correct": True,
                    "behavior": "Ekspert ko'zi bilan qarovchi",
                    "explanation": "✅ To'g'ri! Rasmiy kanallarni faqat rasmiy saytlardan va ko'k belgidan tekshirish kerak."
                },
                {
                    "text": "Avval izohlarni o'qib ko'raman.",
                    "is_correct": False,
                    "behavior": "Ikkilanuvchi",
                    "explanation": "⚠️ Soxta kanallarda izohlar odatda soxta botlar tomonidan maqtovlar bilan to'ldirilgan bo'ladi."
                }
            ]
        },
        {
            "id": 206,
            "title": "Begona odamdan g'alati fayl kelishi",
            "scenario": "Telegramda profilida chiroyli qiz rasmi bo'lgan notanish hisob sizga: 'Mening yangi fotosuratlarim, qara qanday chiqibdi' deb 'my_photo.zip' faylini yubordi.",
            "question": "Faylni ochasizmi?",
            "behavior_type": "curiosity_bait",
            "options": [
                {
                    "text": "Ha, qiziq-ku, rasmlarni ko'raman.",
                    "is_correct": False,
                    "behavior": "Qiziquvchanlik qurboni",
                    "explanation": "❌ Bu rasm emas, arxiv ichidagi kompyuter yoki telefon virusi!"
                },
                {
                    "text": "Faylni yuklab olmayman, foydalanuvchini bloklab spamga tashlayman.",
                    "is_correct": True,
                    "behavior": "Qat'iy xavfsizlik tarafdori",
                    "explanation": "✅ Barakalla! Notanishlardan kelgan .zip, .rar yoki .exe fayllar 99% holatda virus bo'ladi."
                },
                {
                    "text": "Avval telefonga yuklab, keyin do'stimga jo'natib ko'raman.",
                    "is_correct": False,
                    "behavior": "Boshqalarni xavfga qo'yuvchi",
                    "explanation": "❌ Yuklab olishning o'zi xavfli bo'lishi mumkin."
                }
            ]
        },
        {
            "id": 207,
            "title": "Guruhga ruxsatsiz qo'shish (Auto-Add)",
            "scenario": "Sizni har kuni turli notanish reklama, kripto va 'tezkor pul ishlash' guruhlariga ruxsatingizsiz qo'shib tashlashyapti.",
            "question": "Buni to'xtatish uchun nima qilish kerak?",
            "behavior_type": "privacy_settings_knowledge",
            "options": [
                {
                    "text": "Har kuni guruhdan chiqib ketish kerak, boshqa iloj yo'q.",
                    "is_correct": False,
                    "behavior": "Chorasiz / Noiloj",
                    "explanation": "❌ Iloji bor! Telegram maxfiylik sozlamalari mavjud."
                },
                {
                    "text": "Sozlamalar -> Maxfiylik -> Guruhlar va Kanallarga kirib, 'Faqat kontaktlarim' (My Contacts) qilib qo'yaman.",
                    "is_correct": True,
                    "behavior": "Telegramni puxta biluvchi",
                    "explanation": "✅ A'lo! Bu sozlama sizni begonalarning spam guruhlariga qo'shishidan 100% himoya qiladi."
                },
                {
                    "text": "Yangi nomerga yangi Telegram ochish kerak.",
                    "is_correct": False,
                    "behavior": "Radikal va samarasiz",
                    "explanation": "❌ Yangi nomerda ham sozlamani to'g'irlamasangiz yana shu holat takrorlanadi."
                }
            ]
        },
        {
            "id": 208,
            "title": "Telegram orqali pul qarz so'rash",
            "scenario": "Yaqin qarindoshingiz yoki do'stingiz Telegramda: 'Iltimos, juda zarur bo'lib qoldi, kartamga 500,000 so'm tashlab tur, kechqurun qaytaraman' deb yozdi va notanish karta raqamini tashladi.",
            "question": "Sizning birinchi harakatingiz qanday bo'ladi?",
            "behavior_type": "urgency_verification",
            "options": [
                {
                    "text": "Yaqin do'stim bo'lgani uchun darhol ko'rsatilgan kartaga pul o'tkazaman.",
                    "is_correct": False,
                    "behavior": "Tekshirmay ishonuvchi",
                    "explanation": "❌ Katta xato! Do'stingizning profili buzilgan bo'lishi ehtimoli juda yuqori. Pul to'g'ridan-to'g'ri firibgarga ketadi."
                },
                {
                    "text": "Oddiy telefon orqali do'stimning o'ziga qo'ng'iroq qilib, ovozini eshitib aniqlashtiraman.",
                    "is_correct": True,
                    "behavior": "Mustahkam tekshiruvchi",
                    "explanation": "✅ To'g'ri! Moliyaviy so'rovlar doimo jonli qo'ng'iroq orqali tasdiqlanishi shart."
                },
                {
                    "text": "Telegram orqali: 'Rostdan ham sizmisiz?' deb yozaman.",
                    "is_correct": False,
                    "behavior": "Soddadil tekshiruvchi",
                    "explanation": "❌ Profilni o'g'irlagan firibgar: 'Ha, albatta menman' deb javob beradi!"
                }
            ]
        },
        {
            "id": 209,
            "title": "Soxta Telegram Admini",
            "scenario": "Sizga 'Telegram Security Team' degan bot yoki profil yozdi: 'Sizning hisobingiz noqonuniy faoliyatda gumonlanmoqda. Bloklanmaslik uchun mana bu havolada parolingizni tasdiqlang'.",
            "question": "Bu xabarga ishonasizmi?",
            "behavior_type": "authority_intimidation",
            "options": [
                {
                    "text": "Qo'rqib ketaman va bloklanmaslik uchun tezda aytganini qilaman.",
                    "is_correct": False,
                    "behavior": "Qo'rquv ostida boshqariluvchi",
                    "explanation": "❌ Firibgarlar aynan qo'rquv va shoshilish hissiyotingizdan foydalanadi."
                },
                {
                    "text": "Bu soxta xabar! Telegram rasmiy xabarlari maxsus ko'k yulduzli 'Telegram' tizim xabarnomasi orqali keladi va hech qachon shaxsiy chatdan parol so'ramaydi.",
                    "is_correct": True,
                    "behavior": "Tahdidga berilmaydigan",
                    "explanation": "✅ Barakalla! Telegram ma'muriyati hech qachon shaxsiy xabarda parol yoki kod so'ramaydi."
                },
                {
                    "text": "Adminga xat yozib, kechirim so'rayman.",
                    "is_correct": False,
                    "behavior": "Bo'ysunuvchi",
                    "explanation": "❌ Bu firibgarning tuzog'iga battar chuqurroq botish demakdir."
                }
            ]
        },
        {
            "id": 210,
            "title": "Telegram orqali kelgan 'Skrinshot' (Aslida fayl)",
            "scenario": "Sizga Telegramda go'yoki chek rasmi kabi ko'ringan, lekin nomi 'Chek_to'lov.png.apk' yoki '.bat' bo'lgan fayl yuborildi.",
            "question": "Faylni ochish mumkinmi?",
            "behavior_type": "file_extension_awareness",
            "options": [
                {
                    "text": "Ha, bu shunchaki chek rasmi, ko'rishim kerak.",
                    "is_correct": False,
                    "behavior": "E'tiborsiz",
                    "explanation": "❌ Fayl kengaytmasi oxiriga qarang: .apk yoki .bat bu rasm emas, xavfli dastur!"
                },
                {
                    "text": "Yo'q! Bu rasm niqobi ostidagi zararli dastur, darhol o'chiraman.",
                    "is_correct": True,
                    "behavior": "Sinchkov kiber-inspektor",
                    "explanation": "✅ To'g'ri! Haqiqiy rasmlar .jpg, .png yoki .webp bo'ladi, .apk emas."
                },
                {
                    "text": "Faylni ochaman, agar virus bo'lsa telefon o'zi ogohlantiradi.",
                    "is_correct": False,
                    "behavior": "Ortiqcha xotirjam",
                    "explanation": "❌ Telefon doim ham yangi troyanlarni sezmasligi mumkin."
                }
            ]
        }
    ],

    # -------------------------------------------------------------
    # LEVEL 3: Bank Kartalari va To'lov Xavfsizligi (10 ta savol)
    # -------------------------------------------------------------
    3: [
        {
            "id": 301,
            "title": "Kartaning CVV/CVC kodi",
            "scenario": "Onlayn do'kondan narsa sotib olmoqchisiz yoki OLX/Uzum orqali xaridor sizga pul o'tkazmoqchi. U sizdan kartangiz orqasidagi 3 xonali CVV kodni so'rayapti.",
            "question": "Pul qabul qilib olish uchun CVV kod kerakmi?",
            "behavior_type": "banking_basics",
            "options": [
                {
                    "text": "Ha, pul tushishi uchun karta orqasidagi kod ham kerak bo'ladi.",
                    "is_correct": False,
                    "behavior": "Moliyaviy savodsiz",
                    "explanation": "❌ Mutlaqo noto'g'ri! Pul qabul qilib olish uchun FAQAT 16 xonali karta raqami kifoya. CVV faqat pul yechishda ishlatiladi!"
                },
                {
                    "text": "Yo'q! CVV kod faqat pul yechishda ishlatiladi, uni berish — pulni o'g'irlatish demakdir.",
                    "is_correct": True,
                    "behavior": "Moliyaviy savodxon",
                    "explanation": "✅ Barakalla! Pul tushishi uchun hech qachon CVV yoki amal qilish muddati talab qilinmaydi."
                },
                {
                    "text": "Agar xaridor chet eldan pul jo'natayotgan bo'lsa berish mumkin.",
                    "is_correct": False,
                    "behavior": "Xayolparast",
                    "explanation": "❌ Hech qanday xalqaro o'tkazma ham pul qabul qiluvchining CVV kodini talab qilmaydi."
                }
            ]
        },
        {
            "id": 302,
            "title": "Soxta to'lov cheki (Feyk chek bot)",
            "scenario": "Xaridor sizga mahsulot uchun pul to'laganini aytib, Payme yoki Click chekining skrinshotini yubordi. Lekin ilovangizda balans hali oshmagan.",
            "question": "Mahsulotni xaridorga berasizmi?",
            "behavior_type": "proof_verification",
            "options": [
                {
                    "text": "Chekda hamma ma'lumot to'g'ri yozilgan, demak to'lagan, mahsulotni beraman.",
                    "is_correct": False,
                    "behavior": "Skrinshotga aldanuvchi",
                    "explanation": "❌ Telegramda soxta chek yasab beruvchi feyk-botlar to'lib yotibdi. Rasmga ishonish mutlaqo mumkin emas!"
                },
                {
                    "text": "O'z bank ilovamga kirib, hisobimga pul haqiqatda tushganini ko'rmagunimcha bermayman.",
                    "is_correct": True,
                    "behavior": "Faktlarga tayanuvchi",
                    "explanation": "✅ A'lo! Faqat va faqat o'z shaxsiy bank ilovangizdagi real tranzaksiya tarixi to'lovning yagona isbotidir."
                },
                {
                    "text": "Yarmiga ishonib, mahsulotning yarmini berib turaman.",
                    "is_correct": False,
                    "behavior": "Ikkilanuvchi",
                    "explanation": "❌ Bu baribir yo'qotishga olib keladi."
                }
            ]
        },
        {
            "id": 303,
            "title": "Karta rasmini to'liq internetga joylash",
            "scenario": "Do'stingizdan qarz olmoqchisiz va kartangizning oldi va orqa tomonini to'liq rasmga olib, umumiy guruhga tashladingiz.",
            "question": "Buning qanday oqibati bo'ladi?",
            "behavior_type": "reckless_exposure",
            "options": [
                {
                    "text": "Hech narsa bo'lmaydi, PIN-kodini bilishmaydi-ku.",
                    "is_correct": False,
                    "behavior": "Xavfdan bexabar",
                    "explanation": "❌ Ko'plab xalqaro saytlarda (Amazon, AliExpress va b.) PIN-kod va SMS-kodsiz ham xarid qilish mumkin!"
                },
                {
                    "text": "Karta raqami, muddati va CVV orqali kartadagi pulni onlayn xaridlarga ishlatib yuborishlari mumkin.",
                    "is_correct": True,
                    "behavior": "Xavfni to'g'ri baholovchi",
                    "explanation": "✅ To'g'ri! Kartaning fotosuratini hech qachon tarmoqlarga joylash mumkin emas."
                },
                {
                    "text": "Faqat orqa tomonini ko'rsatsam xavfsiz.",
                    "is_correct": False,
                    "behavior": "Chala tushunuvchi",
                    "explanation": "❌ Orqa tomonida aynan eng maxfiy CVV kod joylashgan."
                }
            ]
        },
        {
            "id": 304,
            "title": "'Payme / Click bonus aksiyasi' tuzog'i",
            "scenario": "Sizga SMS yoki xabar keldi: 'Payme 10 yilligi munosabati bilan barcha foydalanuvchilarga 200,000 so'm bonus bermoqda. Bonusni olish uchun mana bu havolada kartangizni tasdiqlang'.",
            "question": "Bu aksiyada qatnashasizmi?",
            "behavior_type": "greed_trap",
            "options": [
                {
                    "text": "Ha, 200 ming so'm yaxshi pul, tezda olib olish kerak.",
                    "is_correct": False,
                    "behavior": "Tekin pulga aldanuvchi",
                    "explanation": "❌ To'lov tizimlari hech qachon karta ma'lumotlarini so'rab 'bonus' bermaydi. Bu soxta fishing sahifa."
                },
                {
                    "text": "Yo'q, bu fishing tuzog'i. Havolani tekshirmasdan darhol o'chiraman.",
                    "is_correct": True,
                    "behavior": "Sog'lom aql sohibi",
                    "explanation": "✅ A'lo! Barcha 'bonus' va 'yutuq' va'da qiluvchi havolalar firibgarlikdir."
                },
                {
                    "text": "Bo'sh kartamni kiritib ko'raman, baribir ichida puli yo'q.",
                    "is_correct": False,
                    "behavior": "Xomxayol",
                    "explanation": "⚠️ Bo'sh karta orqali nomingizga mikromoliya yoki kredit rasmiylashtirib qo'yishlari mumkin!"
                }
            ]
        },
        {
            "id": 305,
            "title": "Karta yo'qolganda tezkor harakat",
            "scenario": "Ko'chada hamyoningiz yoki bank kartangiz tushib qolganini sezdingiz.",
            "question": "Eng birinchi navbatda nima qilish shart?",
            "behavior_type": "crisis_reaction",
            "options": [
                {
                    "text": "Kutaman, balki vijdonli odam topib qaytarib berar.",
                    "is_correct": False,
                    "behavior": "Passiv / Sustkash",
                    "explanation": "❌ Har bir daqiqa g'animat. Topib olgan odam kontaktsiz to'lov (terminal) orqali pulingizni sarflab yuborishi mumkin."
                },
                {
                    "text": "Zudlik bilan bank ilovasiga kirib kartani bloklayman (yoki bankka qo'ng'iroq qilaman).",
                    "is_correct": True,
                    "behavior": "Tezkor va professional",
                    "explanation": "✅ Barakalla! Kartani bloklash — mablag'ni saqlab qolishning birdan-bir yo'lidir."
                },
                {
                    "text": "Ertaga ertalab bankka borib yangi karta ochtiraman.",
                    "is_correct": False,
                    "behavior": "Kechikuvchi",
                    "explanation": "❌ Ertalabgacha kartangizdagi pul qolmasligi mumkin."
                }
            ]
        },
        {
            "id": 306,
            "title": "Kartaga kutilmagan begona pul tushishi",
            "scenario": "Kartangizga to'satdan notanish odamdan 1,000,000 so'm pul tushdi. 5 daqiqadan so'ng birov telefon qilib adashib tashlaganini aytib, boshqa bir begona karta raqamiga qaytarib tashlashni so'radi.",
            "question": "Nima qilasiz?",
            "behavior_type": "money_mule_scam",
            "options": [
                {
                    "text": "Darhol u aytgan begona kartaga o'tkazib beraman.",
                    "is_correct": False,
                    "behavior": "Firibgarlik quroli (Money Mule)",
                    "explanation": "❌ Xavfli sxema! Siz 'dropper' (o'g'irlangan pulni yuvuvchi vositachi)ga aylanib qolasiz va qonuniy javobgarlikka tortilasiz!"
                },
                {
                    "text": "O'zim boshqa kartaga o'tkazmayman, unga bankka murojaat qilishini aytaman yoki bankimga qo'ng'iroq qilib adashgan tranzaksiyani bekor qilishni so'rayman.",
                    "is_correct": True,
                    "behavior": "Qonuniy va xavfsiz yo'l tutuvchi",
                    "explanation": "✅ Mukammal javob! Adashgan mablag' faqat bankning rasmiy arizasi orqali qaytarilishi kerak."
                },
                {
                    "text": "Puling o'zingda qolsin deb pulni o'z ehtiyojlarimga ishlatib yuboraman.",
                    "is_correct": False,
                    "behavior": "Qonunbuzar",
                    "explanation": "❌ Birovning adashib tushgan pulini o'zlashtirish jinoiy javobgarlikka sabab bo'ladi."
                }
            ]
        },
        {
            "id": 307,
            "title": "Kontaktsiz to'lov limiti (NFC / Beep)",
            "scenario": "Kartangizda parolsiz (PIN-kodsiz) to'lash limiti mavjud (masalan, 100,000 so'mgacha terminalda tekshirishsiz o'tadi).",
            "question": "Xavfsizlik uchun qanday tavsiya beriladi?",
            "behavior_type": "limit_management",
            "options": [
                {
                    "text": "Limitni iloji boricha katta qilib qo'ygan yaxshi, qulay bo'ladi.",
                    "is_correct": False,
                    "behavior": "Xavfga befarq",
                    "explanation": "❌ Karta o'g'irlansa, o'g'ri kichik-kichik summalardan bir necha marta parolsiz sarflab yuborishi mumkin."
                },
                {
                    "text": "Bank ilovasida har bir to'lov uchun PIN-kod so'rashni yoki kunlik limitlarni cheklab qo'yish kerak.",
                    "is_correct": True,
                    "behavior": "Nazoratni o'z qo'lida tutuvchi",
                    "explanation": "✅ To'g'ri! Moliyaviy limitlarni boshqarish kutilmagan yo'qotishlarni jilovlaydi."
                },
                {
                    "text": "Kartani faqat folga qog'ozga o'rab yurish kerak.",
                    "is_correct": False,
                    "behavior": "Yuzaki chora",
                    "explanation": "⚠️ Folga radiochastotalardan qisman himoya qilsa-da, haqiqiy xavfsizlik dasturiy limitlardadir."
                }
            ]
        },
        {
            "id": 308,
            "title": "Bankomatda klaviatura va skimmer",
            "scenario": "Bankomatdan pul yechayotganda karta kiritish tirqishida qandaydir qo'shimcha plastmassa moslama yoki klaviaturada shubhali qoplama borligini ko'rdingiz.",
            "question": "Nima qilasiz?",
            "behavior_type": "physical_tampering_awareness",
            "options": [
                {
                    "text": "Hech narsa emas deb kartamni tiqib pul yechaman.",
                    "is_correct": False,
                    "behavior": "E'tiborsiz",
                    "explanation": "❌ Bu 'Skimmer' — kartangiz magnit tasmadagi ma'lumotlarini nusxalovchi firibgarlar uskunasi bo'lishi mumkin!"
                },
                {
                    "text": "Ushbu bankomatdan foydalanmayman, boshqa joyga boraman va bankka xabar beraman.",
                    "is_correct": True,
                    "behavior": "Ehtiyotkor va ijtimoiy mas'uliyatli",
                    "explanation": "✅ A'lo! Shubhali bankomatlardan foydalanmaslik orqali kartangiz klonlanishining oldini olasiz."
                },
                {
                    "text": "Qo'lim bilan yulib olib tashlashga harakat qilaman.",
                    "is_correct": False,
                    "behavior": "Qaltis harakat qiluvchi",
                    "explanation": "⚠️ Bankomatga zarar yetkazmaslik uchun mutaxassislarni ogohlantirish ma'qul."
                }
            ]
        },
        {
            "id": 309,
            "title": "Onlayn xaridlar uchun alohida virtual karta",
            "scenario": "Siz internetdagi turli saytlar va ilovalardan tez-tez narsa sotib olasiz.",
            "question": "Qaysi karta bilan to'lash eng xavfsiz?",
            "behavior_type": "security_segmentation",
            "options": [
                {
                    "text": "Oylik maoshim tushadigan asosiy katta kartam bilan.",
                    "is_correct": False,
                    "behavior": "Hammasini bitta xaltaga soluvchi",
                    "explanation": "❌ Agar sayt ma'lumotlar bazasi buzilsa, barcha oyligingiz bir zumda o'g'irlanadi."
                },
                {
                    "text": "Alohida Virtual karta ochib, faqat xarid summasicha pul tashlab to'layman.",
                    "is_correct": True,
                    "behavior": "Professional xavfsizlik arxitektori",
                    "explanation": "✅ A'lo taktika! Virtual kartada doimo 0 so'm turadi va xarid vaqtida kerakli miqdorda pul o'tkaziladi."
                },
                {
                    "text": "Birovning kartasi bilan to'layman.",
                    "is_correct": False,
                    "behavior": "Mas'uliyatsiz",
                    "explanation": "❌ Bu ham qonuniy, ham axloqiy jihatdan noto'g'ri."
                }
            ]
        },
        {
            "id": 310,
            "title": "SMS-xabarnoma xizmati (SMS Informing)",
            "scenario": "Karta ochganingizda SMS-xabarnoma xizmati oyiga 1000 so'm ekanligini ko'rdingiz.",
            "question": "Pul tejash uchun ushbu xizmatni o'chirib qo'yish to'g'rimi?",
            "behavior_type": "false_economy",
            "options": [
                {
                    "text": "Ha, oyiga 1000 so'm tejasam foyda.",
                    "is_correct": False,
                    "behavior": "Arzimagan pulni tejab kattasidan ayriluvchi",
                    "explanation": "❌ Katta xato! SMS xabarnomasiz kartangizdan pul yechilganda buni bir necha kundan keyin bilib qolasiz va kech bo'ladi."
                },
                {
                    "text": "Yo'q, SMS-xabarnoma doimo yoniq turishi shart — har bir to'lovdan lahzada xabardor bo'laman.",
                    "is_correct": True,
                    "behavior": "Nazoratni doimiy saqlovchi",
                    "explanation": "✅ To'g'ri! Tezkor xabarnoma orqali shubhali to'lovni 1 daqiqa ichida bloklash mumkin."
                },
                {
                    "text": "Faqat kartamda 10 milliondan ko'p pul bo'lsa yoqaman.",
                    "is_correct": False,
                    "behavior": "Mantiqsiz tejamkor",
                    "explanation": "❌ Kichik summali kartalar ham xuddi shunday himoyaga muhtoj."
                }
            ]
        }
    ],

    # -------------------------------------------------------------
    # LEVEL 4: Fishing va Soxta Saytlar (Domenlar) (10 ta savol)
    # -------------------------------------------------------------
    4: [
        {
            "id": 401,
            "title": "Domen nomidagi kichik harf o'zgarishi (Typosquatting)",
            "scenario": "Google orqali Payme saytini qidirib kirdingiz. Manzil satrida 'payme-uz.click' yoki 'paymee.uz' deb yozilgan, dizayni esa xuddi haqiqiy Paymedek.",
            "question": "Bu saytga karta ma'lumotlaringizni kiritasizmi?",
            "behavior_type": "url_vigilance",
            "options": [
                {
                    "text": "Ha, sayt dizayni rasmiy bilan 100% bir xil-ku.",
                    "is_correct": False,
                    "behavior": "Vizual dizaynga aldanuvchi",
                    "explanation": "❌ Firibgarlar sayt dizaynini 1 daqiqada nusxalab oladi. Haqiqiy manzil faqat 'payme.uz' bo'lishi shart!"
                },
                {
                    "text": "Aslo yo'q! Bu soxta typosquatting domeni, darhol sahifani yopaman.",
                    "is_correct": True,
                    "behavior": "Sinchkov kiber-inspektor",
                    "explanation": "✅ To'g'ri! Manzildagi har bitta nuqta va harfni tekshirish — fishingdan himoyaning asosiy omilidir."
                },
                {
                    "text": "Parolni kiritib ko'raman, agar ochilmasa chiqib ketaman.",
                    "is_correct": False,
                    "behavior": "O'zini o'zi tuzoqqa tashlovchi",
                    "explanation": "❌ Bir marta kiritishingiz bilanoq parolingiz firibgar bazasiga tushadi."
                }
            ]
        },
        {
            "id": 402,
            "title": "SSL sertifikat (Qulf belgisi) aldovi",
            "scenario": "Do'stingiz aytdi: 'Sayt manzilida yashil qulf belgisi (HTTPS) tursa, demak bu sayt 100% ishonchli va firibgar emas'.",
            "question": "Ushbu fikr to'g'rimi?",
            "behavior_type": "technical_myth_debunk",
            "options": [
                {
                    "text": "Ha, qulf belgisi tursa sayt davlat tomonidan tekshirilgan va xavfsiz bo'ladi.",
                    "is_correct": False,
                    "behavior": "Texnologik afsonalarga ishonuvchi",
                    "explanation": "❌ Katta xato! Qulf belgisi (HTTPS) bugungi kunda bepul beriladi va firibgarlar ham o'z saytiga qulf belgisini qo'yib oladi. Qulf saytning haqiqiyligini bildirmaydi!"
                },
                {
                    "text": "Yo'q, qulf faqat aloqa shifrlanganini bildiradi, soxta fishing saytlari ham bemalol qulf belgisiga ega bo'lishi mumkin.",
                    "is_correct": True,
                    "behavior": "Chuqur texnik bilimga ega",
                    "explanation": "✅ A'lo bilim! HTTPS sayt egasining halolligiga kafolat bermaydi."
                },
                {
                    "text": "Faqat O'zbekiston saytlarida qulf bo'lsa ishonish mumkin.",
                    "is_correct": False,
                    "behavior": "Hududiy adashuvchi",
                    "explanation": "❌ Qulf texnologiyasi butun dunyoda bir xil ishlaydi."
                }
            ]
        },
        {
            "id": 403,
            "title": "Qisqartirilgan havolalar (bit.ly, t.me/iv...)",
            "scenario": "SMS orqali: 'Sizga jarima yozildi! Tafsilotlar: https://bit.ly/jarima3498' degan xabar keldi.",
            "question": "Ushbu qisqa havolani darhol bosasizmi?",
            "behavior_type": "link_curiosity",
            "options": [
                {
                    "text": "Ha, qanday jarima ekan deb tezda bosib ko'raman.",
                    "is_correct": False,
                    "behavior": "Qo'rquv ostida shoshuvchi",
                    "explanation": "❌ Qisqartirilgan havolalar ortida qayerga olib borishi ko'rinmaydigan xavfli fishing yoki virusli saytlar yashiringan bo'ladi."
                },
                {
                    "text": "Havolani bosmayman, jarimani faqat rasmiy ilovalar (YHXHB, MyGov) orqali tekshiraman.",
                    "is_correct": True,
                    "behavior": "Rasmiy kanallarga tayanuvchi",
                    "explanation": "✅ To'g'ri! Rasmiy davlat organlari bit.ly kabi tekin qisqartirgichlardan foydalanmaydi."
                },
                {
                    "text": "Kompyuterda ochaman, telefonda ochmayman.",
                    "is_correct": False,
                    "behavior": "Noto'g'ri xotirjam",
                    "explanation": "❌ Kompyuter brauzeri ham fishingga tushishi mumkin."
                }
            ]
        },
        {
            "id": 404,
            "title": "Domen zonalari (.uz, .com, .xyz, .top)",
            "scenario": "Uzum Market nomidan yozilgan sayt domeni 'uzum-market-aksiyasi.top' yoki 'uzum.site' deb tugamoqda.",
            "question": "Ushbu domen haqiqiy Uzum'ga tegishlimi?",
            "behavior_type": "tld_awareness",
            "options": [
                {
                    "text": "Ha, Uzum nomi yozilgan-ku.",
                    "is_correct": False,
                    "behavior": "Yuzaki o'quvchi",
                    "explanation": "❌ Domen nomida brend nomining bo'lishi hech narsani anglatmaydi. Muhimi asosiy domen: 'uzum.uz'."
                },
                {
                    "text": "Yo'q, .top, .xyz, .site kabi arzon zonalar firibgarlar tomonidan bir necha kunga ochiladi.",
                    "is_correct": True,
                    "behavior": "Domen arxitekturasini tushunuvchi",
                    "explanation": "✅ Barakalla! O'zbekiston yirik brendlari faqat '.uz' zonasidagi o'z asosiy domenlarida faoliyat yuritadi."
                },
                {
                    "text": "Saytga kirib telefon raqamini solishtirib ko'raman.",
                    "is_correct": False,
                    "behavior": "Ortiqcha tavakkalchi",
                    "explanation": "⚠️ Soxta saytda ham rasmiy telefon raqamlarini ko'rsatib qo'yishlari mumkin."
                }
            ]
        },
        {
            "id": 405,
            "title": "Soxta Davlat Xizmatlari (MyGov / Yagona Portal)",
            "scenario": "Telegramda: 'Prezident qarori bilan har bir fuqaroga 1,500,000 so'mdan moddiy yordam tarqatilmoqda. Olish uchun mygov-yordam.ru saytiga kiring' deb xabar tarqaldi.",
            "question": "Nima qilasiz?",
            "behavior_type": "social_aid_hoax",
            "options": [
                {
                    "text": "Moddiy yordam hammaga berilayotgan bo'lsa, tezda arizani to'ldiraman.",
                    "is_correct": False,
                    "behavior": "Ijtimoiy yordam illyuziyasiga ishonuvchi",
                    "explanation": "❌ Bu eng mashhur firibgarlik to'ri! Davlat rasmiy portali 'my.gov.uz' hisoblanadi, '.ru' emas!"
                },
                {
                    "text": "Bu soxta xabar ekanligini bilaman, havolani hech kimga yubormayman va kirmayman.",
                    "is_correct": True,
                    "behavior": "Axborot gigiyenasiga ega",
                    "explanation": "✅ A'lo! Barcha rasmiy yordamlar faqat rasmiy yangiliklar va my.gov.uz orqali amalga oshiriladi."
                },
                {
                    "text": "Qarindoshlarim va qo'shnilarimga ham tarqataman.",
                    "is_correct": False,
                    "behavior": "Dezinformatsiya tarqatuvchi",
                    "explanation": "❌ Bilmasdan butun mahallangizni firibgar to'riga tushirib qo'yishingiz mumkin."
                }
            ]
        },
        {
            "id": 406,
            "title": "Brauzerda soxta 'Google bilan kirish' (OAuth pop-up)",
            "scenario": "Biror saytga kirganingizda kichik oyna ochilib 'Sign in with Google' (Google orqali kiring) dedi. Lekin oynaning manzil satri 'google.com' emas, balki shubhali boshqa sayt manzili.",
            "question": "Google emailingiz va parolingizni kiritasizmi?",
            "behavior_type": "popup_spoofing",
            "options": [
                {
                    "text": "Ha, odatiy Google orqali kirish tugmasi-ku.",
                    "is_correct": False,
                    "behavior": "Oynaning asl manziliga qaramaydigan",
                    "explanation": "❌ Bu 'Browser-in-the-Browser' (BitB) hujumi! Oyna tashqi ko'rinishidan Googlega o'xshatilgan soxta HTML blokdir."
                },
                {
                    "text": "Yo'q, haqiqiy Google avtorizatsiya oynasi faqat 'accounts.google.com' manzilida bo'ladi.",
                    "is_correct": True,
                    "behavior": "Kiber-ekspert darajasida ehtiyotkor",
                    "explanation": "✅ A'lo daraja! Avtorizatsiya oynasining manzilini tekshirmasdan parol kiritilmaydi."
                },
                {
                    "text": "Boshqa ijtimoiy tarmoq bilan kirib ko'raman.",
                    "is_correct": False,
                    "behavior": "Chala xavfsiz",
                    "explanation": "❌ Boshqa tarmoq oynasi ham soxta bo'lishi mumkin."
                }
            ]
        },
        {
            "id": 407,
            "title": "Saytda 'Telefoningizga 13 ta virus tushdi!' degan vahima xabari",
            "scenario": "Internetda yangilik o'qiyotganingizda qizil fon bilan ekran qaltirab: 'DIQQAT! Telefoningiz zararlangan! Batareya 2 daqiqada portlaydi! Tezda tozalovchi dasturni yuklang!' degan oyna chiqdi.",
            "question": "Qanday yo'l tutasiz?",
            "behavior_type": "scareware_panic",
            "options": [
                {
                    "text": "Qo'rqib ketib, ko'rsatilgan 'Tozalash' tugmasini darhol bosaman.",
                    "is_correct": False,
                    "behavior": "Vahimaga oson beriluvchi (Scareware qurboni)",
                    "explanation": "❌ Bu 'Scareware' deb ataladi! Sayt sizning telefoningiz ichini ko'ra olmaydi. U shunchaki vahima qo'zg'ab, haqiqiy virusni o'rnatmoqchi!"
                },
                {
                    "text": "Brauzer oynasini (tab) shunchaki yopib tashlayman, hech narsa yuklamayman.",
                    "is_correct": True,
                    "behavior": "Sovuqqon va aqlli",
                    "explanation": "✅ To'g'ri! Bu oddiy reklama sahifasi. Tabni yopish orqali xavf darhol bartaraf etiladi."
                },
                {
                    "text": "Telefonni o'chirib, ustaga olib boraman.",
                    "is_correct": False,
                    "behavior": "Ortiqcha vahimachi",
                    "explanation": "⚠️ Vahimaga o'rin yo'q, shunchaki brauzer oynasini yopish kifoya."
                }
            ]
        },
        {
            "id": 408,
            "title": "Onlayn do'konda shubhali arzon narxlar",
            "scenario": "Instagramda reklama chiqdi: 'iPhone 15 Pro Max atigi 3,000,000 so'm! Faqat bugun ombor tozalash aksiyasi!' Saytga kirsangiz faqat oldindan 100% to'lov qabul qilinadi.",
            "question": "Xarid qilasizmi?",
            "behavior_type": "unrealistic_discount_trap",
            "options": [
                {
                    "text": "Albatta, bunaqa narx boshqa bo'lmaydi, darhol to'layman.",
                    "is_correct": False,
                    "behavior": "Arzonchilik ortidan quvuvchi",
                    "explanation": "❌ Bozor narxidan 4-5 barobar arzon mahsulot 100% holatda yo'q narsa yoki firibgarlikdir. Pulingiz kuyadi."
                },
                {
                    "text": "Yo'q, bu soxta bir kunlik do'kon (Fake Shop). Hech qanday pul to'lamayman.",
                    "is_correct": True,
                    "behavior": "Realist va ehtiyotkor",
                    "explanation": "✅ To'g'ri! Agar taklif haqiqatga to'g'ri kelmaydigan darajada yaxshi bo'lsa — bu aniq firibgarlik."
                },
                {
                    "text": "Do'konga yozib, yana ozroq tushirib berishini so'rayman.",
                    "is_correct": False,
                    "behavior": "Soddadil savdogar",
                    "explanation": "❌ Ular sizga yanada arzon qilib, pulingizni tezroq olishga rozi bo'ladi."
                }
            ]
        },
        {
            "id": 409,
            "title": "Email orqali kelgan 'Parolingiz muddati tugadi'",
            "scenario": "Pochtanggizga 'Google Support' nomidan xat keldi: 'Parolingiz bugun tugaydi, uni yangilash uchun havolaga bosing'. Havola manzili esa 'sec-google-pass.net'.",
            "question": "Nima qilasiz?",
            "behavior_type": "email_phishing",
            "options": [
                {
                    "text": "Havolaga kirib, eski va yangi parolimni yozaman.",
                    "is_correct": False,
                    "behavior": "Email jo'natuvchi manziliga e'tiborsiz",
                    "explanation": "❌ Jo'natuvchining haqiqiy domeniga qarang: '.net'. Google hech qachon shunday shubhali domenlardan xat yozmaydi."
                },
                {
                    "text": "Xatni o'chirib tashlayman va jo'natuvchini bloklayman.",
                    "is_correct": True,
                    "behavior": "Email kiber-gigiyenasiga rioya qiluvchi",
                    "explanation": "✅ A'lo! Hech qachon xatdagi shubhali havolalar orqali parol yangilanmaydi."
                },
                {
                    "text": "Xatga javob yozib: 'Rostdan ham sizmisiz?' deb so'rayman.",
                    "is_correct": False,
                    "behavior": "Befoyda muloqot qiluvchi",
                    "explanation": "❌ Firibgarlar o'z botlari orqali javob berishadi."
                }
            ]
        },
        {
            "id": 410,
            "title": "Xavfli havolani ShieldGuard orqali tekshirish",
            "scenario": "Sizga internetda qandaydir noma'lum havola yuborildi va uning xavfsiz ekanligiga shubhangiz bor.",
            "question": "Eng to'g'ri va zamonaviy usul qaysi?",
            "behavior_type": "tool_utilization",
            "options": [
                {
                    "text": "Havolani tavakkal bosib, ko'rib chiqaman.",
                    "is_correct": False,
                    "behavior": "Tavakkalchi",
                    "explanation": "❌ Bir marta bosish ham fishing yoki ziyon keltirishi mumkin."
                },
                {
                    "text": "Havolani nusxalab, ShieldGuard AI botiga yoki rasmiy tekshiruv vositalariga yuborib tahlil qildiraman.",
                    "is_correct": True,
                    "behavior": "Professional vositalardan foydalanuvchi",
                    "explanation": "✅ Mukammal qaror! ShieldGuard sun'iy intellekti domen xavfsizligini 1 soniyada tekshirib beradi."
                },
                {
                    "text": "Do'stimga tashlab, 'sen bosib ko'rchi nima ekan' deyman.",
                    "is_correct": False,
                    "behavior": "Do'stini xavf ostiga qo'yuvchi",
                    "explanation": "❌ Do'stingiz qurilmasiga zarar yetishi mumkin."
                }
            ]
        }
    ],

    # -------------------------------------------------------------
    # LEVEL 5: Zararli APK va Android Troyanlar (10 ta savol)
    # -------------------------------------------------------------
    5: [
        {
            "id": 501,
            "title": "Telegramda kelgan 'Taklifnoma.apk'",
            "scenario": "Guruhda notanish raqamdan xabar: 'To'yimizga taklif qilamiz, manzil va taklifnoma dasturda: Taklifnoma.apk'.",
            "question": "Ushbu APK faylni yuklab o'rnatasizmi?",
            "behavior_type": "apk_trojan_awareness",
            "options": [
                {
                    "text": "Ha, to'y qayerda ekanini bilish uchun o'rnataman.",
                    "is_correct": False,
                    "behavior": "Troyan qurboni",
                    "explanation": "❌ Bu O'zbekistonda eng keng tarqalgan bank troyani! Fotosurat yoki taklifnoma hech qachon .apk (dastur) bo'lmaydi."
                },
                {
                    "text": "Yo'q! Bu bank kartalaridan pul o'g'irlovchi troyan virus, zudlik bilan o'chirib tashlayman.",
                    "is_correct": True,
                    "behavior": "Texnologik hushyor",
                    "explanation": "✅ Barakalla! .apk fayllarini faqat rasmiy Play Market'dan olish kerak."
                },
                {
                    "text": "O'rnataman, agar virus bo'lsa telefonim ruxsat so'raydi.",
                    "is_correct": False,
                    "behavior": "Xavfli ishonch",
                    "explanation": "❌ O'rnatish jarayonida foydalanuvchining o'zi bilmasdan barcha ruxsatlarni berib yuborishi mumkin."
                }
            ]
        },
        {
            "id": 502,
            "title": "Maxsus Imkoniyatlar (Accessibility Services) ruxsati",
            "scenario": "Telefonga o'rnatilgan yangi dastur sozlamalardan 'Maxsus imkoniyatlar' (Accessibility / Доступность) xizmatini yoqishingizni talab qilmoqda.",
            "question": "Ushbu ruxsatni berish xavflimi?",
            "behavior_type": "permission_risk_understanding",
            "options": [
                {
                    "text": "Hech qisi yo'q, ilova ishlashi uchun so'rayapti-ku.",
                    "is_correct": False,
                    "behavior": "Ruxsatlarga befarq",
                    "explanation": "❌ Accessibility ruxsati berilsa, troyan ekrandagi barcha parollaringizni ko'radi, klaviatura bosilishini yozib oladi va sizning nomingizdan bank to'lovlarini bosadi!"
                },
                {
                    "text": "Juda xavfli! Faqat ko'zi ojizlar uchun maxsus rasmiy ilovalar bundan mustasno, oddiy ilovalarga bu ruxsat aslo berilmaydi.",
                    "is_correct": True,
                    "behavior": "Kiber-xavfsizlik mezonlarini biluvchi",
                    "explanation": "✅ A'lo! Accessibility ruxsati — troyanlarga telefonni to'liq boshqarish imkonini beruvchi eng xavfli ruxsatdir."
                },
                {
                    "text": "Faqat kunduzi yoqib, kechasi o'chirib qo'yaman.",
                    "is_correct": False,
                    "behavior": "Mantiqsiz yondashuv",
                    "explanation": "❌ Troyanga 1 soniya yetarli bo'ladi."
                }
            ]
        },
        {
            "id": 503,
            "title": "Modifikatsiyalangan Telegram/WhatsApp ilovalari",
            "scenario": "Do'stingiz tavsiya qildi: 'O'chirilgan xabarlarni o'qish va bepul funksiyalar uchun 'Telegram Plus Mod VIP' degan APK ni o'rnatib ol'.",
            "question": "Norasmiy modifikatsiyalangan ilovalardan foydalanish xavfsizmi?",
            "behavior_type": "modded_app_risk",
            "options": [
                {
                    "text": "Ha, juda ko'p qulayliklari bor, hamma ishlatadi.",
                    "is_correct": False,
                    "behavior": "Qulaylik ortidan xavfga botuvchi",
                    "explanation": "❌ Norasmiy modlar mualliflari sizning yozishmalaringiz, kontaktlaringiz va media fayllaringizni o'z serverlariga yashirincha ko'chiradi."
                },
                {
                    "text": "Yo'q, bu ilovalar xakerlar tomonidan qayta yozilgan bo'lib, akkaunt o'g'irlanishiga sabab bo'ladi.",
                    "is_correct": True,
                    "behavior": "Asl nusxani afzal ko'ruvchi",
                    "explanation": "✅ To'g'ri! Faqat rasmiy dasturchidan Play Market yoki App Store orqali yuklangan rasmiy ilovalardan foydalanish kerak."
                },
                {
                    "text": "Faqat yozishish uchun ishlatib, rasmlar jo'natmayman.",
                    "is_correct": False,
                    "behavior": "Chala himoya",
                    "explanation": "❌ Matnli xabarlarda ham maxfiy ma'lumotlar bo'ladi."
                }
            ]
        },
        {
            "id": 504,
            "title": "SMS xabarlarni o'qish (READ_SMS) ruxsati",
            "scenario": "Oddiy kalkulyator yoki chiroq (fonarik) ilovasi sizdan 'SMS xabarlarni o'qish va yuborish' ruxsatini so'ramoqda.",
            "question": "Kalkulyatorga SMS o'qish ruxsati kerakmi?",
            "behavior_type": "permission_logic_check",
            "options": [
                {
                    "text": "Ilova so'rayaptimi, demak kerak, 'Ruxsat berish'ni bosaman.",
                    "is_correct": False,
                    "behavior": "So'rovlarni o'qimay tasdiqlovchi",
                    "explanation": "❌ Kalkulyatorga SMS o'qish umuman kerak emas! Bu 100% bank SMS kodlarini o'g'irlovchi yashirin troyandir."
                },
                {
                    "text": "Aslo ruxsat bermayman va bu ilovani darhol o'chirib tashlayman.",
                    "is_correct": True,
                    "behavior": "Mantiqiy tahlil qiluvchi",
                    "explanation": "✅ Barakalla! Ilovaning vazifasiga to'g'ri kelmaydigan shubhali ruxsatlar xavfdan darak beradi."
                },
                {
                    "text": "Ruxsat beraman, lekin ilovadan kamroq foydalanaman.",
                    "is_correct": False,
                    "behavior": "Beparvo",
                    "explanation": "❌ Ilova fonda o'zi mustaqil SMSlarni o'g'irlayveradi."
                }
            ]
        },
        {
            "id": 505,
            "title": "Play Protect ogohlantirishini e'tiborsiz qoldirish",
            "scenario": "Tashqaridan APK o'rnatayotganingizda Google Play Protect qizil ogohlantirish berdi: 'Ushbu ilova zararli va shaxsiy ma'lumotlarni o'g'irlashi mumkin'.",
            "question": "'Baribir o'rnatish' (Install anyway) tugmasini bosasizmi?",
            "behavior_type": "security_bypass_temptation",
            "options": [
                {
                    "text": "Ha, Google doim shunaqa deb asabga tegadi, o'rnatish kerak.",
                    "is_correct": False,
                    "behavior": "Himoya tizimini mensimaydigan",
                    "explanation": "❌ Google Play Protect bekorga qizil ogohlantirish bermaydi. Ushbu dastur ma'lumotlar bazasida zararli deb ro'yxatga olingan."
                },
                {
                    "text": "Yo'q, o'rnatishni darhol bekor qilaman va yuklangan faylni o'chiraman.",
                    "is_correct": True,
                    "behavior": "Signalga to'g'ri reaksiya beruvchi",
                    "explanation": "✅ To'g'ri! Antivirus ogohlantirishlariga beparvo bo'lish halokatli oqibatga olib keladi."
                },
                {
                    "text": "Telefonimni o'chirib-yoqib yana qaytadan o'rnatishga urinaman.",
                    "is_correct": False,
                    "behavior": "O'jar xato qiluvchi",
                    "explanation": "❌ O'jar ravishda virus o'rnatish xavfsizlikka ziddir."
                }
            ]
        },
        {
            "id": 506,
            "title": "Ilova ikonkasining yashirinib qolishi",
            "scenario": "Biror faylni o'rnatdingiz, lekin ekranda uning belgisi (ikonkasi) ko'rinmay qoldi. Ammo telefoningiz qizib, internet trafigi tez ketyapti.",
            "question": "Bu nimani anglatadi?",
            "behavior_type": "hidden_malware_symptoms",
            "options": [
                {
                    "text": "Dastur o'rnatilmay qolibdi, hech qisi yo'q.",
                    "is_correct": False,
                    "behavior": "Belgilarga e'tiborsiz",
                    "explanation": "❌ Xato! Troyan o'z belgisini yashirib olgan va fonda yashirin ishlamoqda."
                },
                {
                    "text": "Zararli dastur o'zini yashirgan. Sozlamalar -> Ilovalar (Apps) ro'yxatiga kirib, nomsiz yoki shubhali ilovani topib o'chirish kerak.",
                    "is_correct": True,
                    "behavior": "Diagnostik bilimga ega",
                    "explanation": "✅ A'lo! Ko'p troyanlar shaffof ikonka va nomsiz bo'lib tizimda yashirinib oladi."
                },
                {
                    "text": "Telefonim eskirib qolibdi, yangisini sotib olishim kerak.",
                    "is_correct": False,
                    "behavior": "Muammoni noto'g'ri tushunuvchi",
                    "explanation": "⚠️ Muammo telefonda emas, o'rnatilgan zararli kodda."
                }
            ]
        },
        {
            "id": 507,
            "title": "Noma'lum manbalardan o'rnatish (Unknown Sources)",
            "scenario": "Telefon sozlamalarida 'Noma'lum manbalardan dastur o'rnatishga ruxsat' (Install from unknown sources) funksiyasi mavjud.",
            "question": "Ushbu sozlama doimo yoqilgan holda turishi to'g'rimi?",
            "behavior_type": "system_hardening",
            "options": [
                {
                    "text": "Ha, xohlagan joydan bemalol o'yin va dastur tortaverish uchun qulay.",
                    "is_correct": False,
                    "behavior": "Himoyani ataylab zaiflashtiruvchi",
                    "explanation": "❌ Bu telefoningiz xavfsizlik devorini butunlay ochib qo'yish demakdir."
                },
                {
                    "text": "Yo'q, u doimo o'chirilgan (bloklangan) bo'lishi kerak.",
                    "is_correct": True,
                    "behavior": "Tizimni mustahkamlovchi",
                    "explanation": "✅ To'g'ri! Faqat zarur bo'lgandagina vaqtincha yoqilib, darhol o'chirib qo'yilishi shart."
                },
                {
                    "text": "Faqat kechalari o'chirib qo'yaman.",
                    "is_correct": False,
                    "behavior": "Yuzaki rejim",
                    "explanation": "❌ Hujumlar kunduzi ham sodir bo'ladi."
                }
            ]
        },
        {
            "id": 508,
            "title": "APK faylni antivirus bilan tekshirish",
            "scenario": "Do'stingiz foydali deb yuborgan APK faylini o'rnatishdan oldin tekshirmoqchisiz.",
            "question": "Buni qanday amalga oshirish eng to'g'ri?",
            "behavior_type": "file_scanning_tools",
            "options": [
                {
                    "text": "Fayl nomiga qarayman, chiroyli yozilgan bo'lsa o'rnataman.",
                    "is_correct": False,
                    "behavior": "Nomi orqali baholovchi",
                    "explanation": "❌ Firibgarlar eng mashhur dasturlar nomidan foydalanishadi."
                },
                {
                    "text": "Faylni 'VirusTotal' saytiga yoki ShieldGuard APK tekshiruvchisiga yuklab, 70 ta antivirus bilan tekshirtiraman.",
                    "is_correct": True,
                    "behavior": "Ilg'or tahlilchi",
                    "explanation": "✅ A'lo! VirusTotal va ShieldGuard bir zumda fayl ichidagi troyan signaturalarini fosh qiladi."
                },
                {
                    "text": "Fayl hajmi 10 MB dan kam bo'lsa xavfsiz deb hisoblayman.",
                    "is_correct": False,
                    "behavior": "Hajmga qarab xulosa chiqaruvchi",
                    "explanation": "❌ Eng xavfli troyanlar atigi 200 KB hajmda bo'ladi."
                }
            ]
        },
        {
            "id": 509,
            "title": "Kamera va Mikrofonga doimiy ruxsat so'rash",
            "scenario": "Oddiy ob-havo (Weather) dasturi o'rnatilgach, doimiy ravishda fonda kamerangizdan va mikrofoningizdan foydalanishga ruxsat so'radi.",
            "question": "Nima qilasiz?",
            "behavior_type": "spying_awareness",
            "options": [
                {
                    "text": "Ruxsat beraman, ob-havoni aniqlash uchun kerakdir.",
                    "is_correct": False,
                    "behavior": "Josuslikka yo'l qo'yuvchi",
                    "explanation": "❌ Ob-havo ilovasiga kamera yoki mikrofon umuman kerak emas! Bu yashirin josus dastur (Spyware) bo'lishi mumkin."
                },
                {
                    "text": "Ruxsat bermayman va bunday shubhali ilovani o'chirib tashlayman.",
                    "is_correct": True,
                    "behavior": "Shaxsiy hayot daxlsizligini asrovchi",
                    "explanation": "✅ Barakalla! Ilovalarga faqat o'z vazifasiga mos ruxsatlar berilishi kerak."
                },
                {
                    "text": "Kameraga ruxsat beraman, mikrofonga bermayman.",
                    "is_correct": False,
                    "behavior": "Mantiqsiz murosachi",
                    "explanation": "❌ Kamera ham o'ta xavfli maxfiy ma'lumot manbaidir."
                }
            ]
        },
        {
            "id": 510,
            "title": "Android tizimini 'Root' (Superuser) qilish",
            "scenario": "Internetda tavsiya qilishdi: 'Telefoningizni Root qilsangiz barcha o'yinlarni tekin qilasiz va cheklovlarsiz ishlatasiz'.",
            "question": "Telefonni Root qilish xavfsizlikka qanday ta'sir qiladi?",
            "behavior_type": "root_jailbreak_consequences",
            "options": [
                {
                    "text": "Juda zo'r bo'ladi, telefon kuchayadi.",
                    "is_correct": False,
                    "behavior": "Xavf tubiga yetmagan",
                    "explanation": "❌ Root qilingan telefonda bank ilovalari ishlamay qoladi va har qanday oddiy virus telefoningizni to'liq o'z nazoratiga oladi!"
                },
                {
                    "text": "Tizimning barcha xavfsizlik qatlamlari buziladi va viruslar uchun mutlaq erkinlik yaratiladi.",
                    "is_correct": True,
                    "behavior": "Tizim yaxlitligini qadrlovchi",
                    "explanation": "✅ To'g'ri! Root qilingan telefon kiber-jinoyatchilar uchun eng oson o'ljadir."
                },
                {
                    "text": "Faqat xitoy telefonlarida xavfli, boshqalarida xavfsiz.",
                    "is_correct": False,
                    "behavior": "Mish-mishlarga ishonuvchi",
                    "explanation": "❌ Har qanday brenddagi Android qurilmasi Root qilinganda xavfsizligini yo'qotadi."
                }
            ]
        }
    ],

    # -------------------------------------------------------------
    # LEVEL 6: Ijtimoiy Muhandislik va Psixologik Bosim (10 ta savol)
    # -------------------------------------------------------------
    6: [
        {
            "id": 601,
            "title": "Soxta tergovchi yoki IIB xodimi qo'ng'irog'i",
            "scenario": "Qo'ng'iroq qilib qat'iy va rasmiy ohangda: 'Men IIB Tergov boshqarmasi kapitani Falonchiyevman. Sizning nomingizdan noqonuniy terrorchilik operatsiyalari o'tmoqda. Jinoyat ishi ochilmasligi uchun zudlik bilan barcha kartangiz ma'lumotlarini aytishingiz kerak!' deyishdi.",
            "question": "Sizning munosabatingiz?",
            "behavior_type": "fear_intimidation",
            "options": [
                {
                    "text": "Qo'rqib ketaman, qamalib ketmaslik uchun barcha ma'lumotlarimni aytaman.",
                    "is_correct": False,
                    "behavior": "Qo'rquv ostida falajlanuvchi",
                    "explanation": "❌ Bu eng xavfli psixologik tuzoq! IIB yoki huquq-tartibot organlari hech qachon telefon orqali karta parolini so'ramaydi va tergov qilmaydi."
                },
                {
                    "text": "Aloqani uzaman va: 'Rasmiy chaqiruv qog'ozi (povestka) yuboring, bo'limga o'zim boraman' deyman.",
                    "is_correct": True,
                    "behavior": "Ruhiy bosimga bardoshli",
                    "explanation": "✅ A'lo daraja! Qonuniy tergov faqat rasmiy chaqiruv qog'ozi orqali bino ichida advokat ishtirokida olib boriladi."
                },
                {
                    "text": "Ular bilan bahslashib, pul taklif qilaman.",
                    "is_correct": False,
                    "behavior": "Vaziyatni chigallashtiruvchi",
                    "explanation": "⚠️ Bu firibgarga yanada ko'proq manipulyatsiya dastagini beradi."
                }
            ]
        },
        {
            "id": 602,
            "title": "Sun'iy shoshilinchlik hissi (5 daqiqa qoldi!)",
            "scenario": "Firibgar: 'Sizning hisobingizdan hozir 5,000,000 so'm yechilyapti! Agar 2 daqiqa ichida kodni aytmasangiz pulingiz butunlay kuyadi!' deb shoshiltirmoqda.",
            "question": "Nega firibgar sizni shoshiltiradi?",
            "behavior_type": "urgency_manipulation",
            "options": [
                {
                    "text": "Haqiqatdan ham menga yordam bermoqchi va vaqt oz qolgan.",
                    "is_correct": False,
                    "behavior": "Yordam niqobiga ishonuvchi",
                    "explanation": "❌ Shoshiltirish — miyaning mantiqiy fikrlash markazini o'chirib, emotsional xato qilishga majburlash usulidir."
                },
                {
                    "text": "Menga o'ylashga va tekshirishga vaqt qoldirmaslik, qo'rquv orqali kodni undirish uchun.",
                    "is_correct": True,
                    "behavior": "Psixologik tuzoqni ko'ra oluvchi",
                    "explanation": "✅ To'g'ri! Agar sizni haddan tashqari shoshiltirishsa — demak bu 100% tuzoq."
                },
                {
                    "text": "Bank qoidalari shunaqa qattiq bo'lsa kerak.",
                    "is_correct": False,
                    "behavior": "Tizimni noto'g'ri tasavvur qiluvchi",
                    "explanation": "❌ Bank o'z tizimida shubhali operatsiyani mustaqil to'xtata oladi."
                }
            ]
        },
        {
            "id": 603,
            "title": "Yaqin qarindosh falokatga uchragani haqida soxta xabar",
            "scenario": "Kechasi notanish raqam qo'ng'iroq qilib, yig'lagan ovozda: 'Ona/Ota, men avtohalokatga uchradim, birovni urib yubordim! Qamalmasligim uchun tergovchiga tezda 20 million so'm yetkazish kerak!' deyildi.",
            "question": "Bunday dahshatli xabarda nima qilasiz?",
            "behavior_type": "family_panic_exploit",
            "options": [
                {
                    "text": "Vahimaga tushib, uydagi bor pulni taksi orqali aytilgan manzilga jo'nataman.",
                    "is_correct": False,
                    "behavior": "Hissiyotlarga yengiluvchi",
                    "explanation": "❌ Bu ko'plab ota-onalarni qaqshatgan klassik firibgarlik! Ovoz ko'pincha aktyor yoki AI kloni bo'ladi."
                },
                {
                    "text": "Chuqur nafas olib xotirjamlikni saqlayman, zudlik bilan farzandimning o'z telefoniga va yaqinlariga qo'ng'iroq qilib tekshiraman.",
                    "is_correct": True,
                    "behavior": "Krizis holatida sovuqqon",
                    "explanation": "✅ Qahramonona qaror! 99% holatda farzandingiz uxlab yotgan yoki bexabar bo'ladi."
                },
                {
                    "text": "Tergovchiga kamroq pulga kelishishni iltimos qilaman.",
                    "is_correct": False,
                    "behavior": "Tuzoq ichida savdolashuvchi",
                    "explanation": "❌ Bu firibgarning o'ljasiga aylanishingizni tasdiqlaydi."
                }
            ]
        },
        {
            "id": 604,
            "title": "Soxta xayriya va kasal bolalar fotosuratlari",
            "scenario": "Ijtimoiy tarmoqda yurakni ezuvchi rasm bilan: 'Ushbu norasida go'dakka zudlik bilan operatsiya kerak, 1 soat vaqt qoldi!' deb shaxsiy karta raqami qo'yilgan.",
            "question": "Ushbu kartaga tekshirmasdan pul o'tkazasizmi?",
            "behavior_type": "charity_scam",
            "options": [
                {
                    "text": "Ha, bolaga rahmim keldi, ehson qilaman.",
                    "is_correct": False,
                    "behavior": "Hissiyotdan foydalanuvchilar o'ljasi",
                    "explanation": "❌ Firibgarlar internetdan begona xorijiy kasal bolalar rasmlarini o'g'irlab, o'z shaxsiy kartalarini qo'yib pul yig'ishadi."
                },
                {
                    "text": "Faqat rasmiy davlat ro'yxatidan o'tgan xayriya fondlari (Ezgu Amal va b.) orqali ehson qilaman.",
                    "is_correct": True,
                    "behavior": "Aqlli va manzilli ehson qiluvchi",
                    "explanation": "✅ To'g'ri! Haqiqiy ehson faqat tekshirilgan va hisobdor tashkilotlar orqali qilinishi kerak."
                },
                {
                    "text": "Post tagida yomon izohlar yozib qoldiraman.",
                    "is_correct": False,
                    "behavior": "Samarasiz harakat",
                    "explanation": "⚠️ Izoh yozish postning ko'proq tarqalishiga (algoritmga) yordam berib yuboradi."
                }
            ]
        },
        {
            "id": 605,
            "title": "Romantik firibgarlik (Catfishing / Love Scam)",
            "scenario": "Internetda chiroyli chet ellik (yoki boy biznesmen) siz bilan 1 oy iliq gaplashdi, sevgisini izhor qildi. Keyin 'Senga qimmatbaho sovg'a va tilla jo'natdim, lekin bojxonada ushlab qolindi, 300 dollar to'lovini to'lab yubor' dedi.",
            "question": "Pulni to'laysizmi?",
            "behavior_type": "romance_fraud",
            "options": [
                {
                    "text": "Sevgan insonimga yordam qilish uchun qarz olib bo'lsa ham to'layman.",
                    "is_correct": False,
                    "behavior": "Ishqiy illyuziyaga aldanuvchi",
                    "explanation": "❌ Bu xalqaro 'Love Scam'! Hech qanday sovg'a yo'q, o'sha 'go'zal' profil ortida uyushgan firibgarlar guruhi o'tiribdi."
                },
                {
                    "text": "Bu klassik romantik firibgarlik ekanligini anglab, darhol aloqani uzaman.",
                    "is_correct": True,
                    "behavior": "Hissiy manipulyatsiyaga tushmaydigan",
                    "explanation": "✅ A'lo! Hayotda ko'rmagan virtual odamlarga moddiy mablag' jo'natish fojiaga olib keladi."
                },
                {
                    "text": "Sovg'a yetib kelgach to'layman deb aldab turaman.",
                    "is_correct": False,
                    "behavior": "Befoyda muzokara",
                    "explanation": "⚠️ Firibgar baribir sizdan pul undirishga urinishda davom etadi."
                }
            ]
        },
        {
            "id": 606,
            "title": "Avtoritetga ko'r-ko'rona itoat qilish",
            "scenario": "Sizga o'zini 'Markaziy Bank departament boshlig'i' deb tanishtirgan shaxs barcha banklarning yagona bazasi yangilanayotganini aytib, sizning shaxsiy sirlaringizni talab qildi.",
            "question": "Katta lavozimli shaxsga so'zsiz ishonish kerakmi?",
            "behavior_type": "authority_bias",
            "options": [
                {
                    "text": "Katta rahbar ekan, yolg'on gapirmasa kerak deb aytaman.",
                    "is_correct": False,
                    "behavior": "Lavozimdan hayiqib bo'ysunuvchi",
                    "explanation": "❌ Firibgarlar odatda o'zlarini eng nufuzli tashkilotlar (Prezident Administratsiyasi, DXX, Markaziy Bank) nomidan tanishtirishadi."
                },
                {
                    "text": "Har qanday lavozim egasi bo'lishidan qat'i nazar, shaxsiy ma'lumotlarni hech kimga berish mumkin emas.",
                    "is_correct": True,
                    "behavior": "Prinsipial xavfsizlik himoyachisi",
                    "explanation": "✅ Barakalla! Haqiqiy davlat amaldorlari fuqarolarga qo'ng'iroq qilib parol so'ramaydi."
                },
                {
                    "text": "Faqat qaysi kabinetda o'tirishini so'rayman.",
                    "is_correct": False,
                    "behavior": "Yuzaki tekshiruv",
                    "explanation": "❌ Ular internetdan barcha kabinet raqamlarini yodlab olgan bo'lishadi."
                }
            ]
        },
        {
            "id": 607,
            "title": "O'zaro xizmat hissi (Reciprocity trap)",
            "scenario": "Notanish odam Telegramda sizga tekin foydali kitob yoki pullik kursni sovg'a qildi. 2 kundan so'ng: 'Do'stim, senga yordam bergandim, endi sen ham kartangga kelgan bitta kodni aytib yubor' dedi.",
            "question": "Qarzdorlik hissi tufayli kodni berasizmi?",
            "behavior_type": "reciprocity_manipulation",
            "options": [
                {
                    "text": "U menga yaxshilik qildi, men ham rad eta olmayman.",
                    "is_correct": False,
                    "behavior": "Axloqiy qarz tuzog'iga tushuvchi",
                    "explanation": "❌ Bu 'Reciprocity' psixologik tuzog'idir! Boshida kichik tekin narsa berib, keyin katta narsani tortib olishadi."
                },
                {
                    "text": "Xavfsizlik qoidalariga xiyonat qilmayman — kod berish mutlaqo taqiqlangan.",
                    "is_correct": True,
                    "behavior": "Chegarani qat'iy saqlovchi",
                    "explanation": "✅ To'g'ri! Hech qanday sovg'a shaxsiy xavfsizlik hisobiga to'lanmaydi."
                },
                {
                    "text": "Kodni berib, unga rahmat aytaman.",
                    "is_correct": False,
                    "behavior": "O'ta sodda",
                    "explanation": "❌ Natijada kartangiz bo'shaydi."
                }
            ]
        },
        {
            "id": 608,
            "title": "Shantaj va shaxsiy sirlarni tarqatish tahdidi",
            "scenario": "Sizga xat keldi: 'Kamerangiz orqali shaxsiy noqulay holatingizni videoga olib oldik! 24 soat ichida 500$ to'lamasangiz barcha qarindoshlaringizga yuboramiz!'.",
            "question": "Ushbu tahdidga nima deb javob berasiz?",
            "behavior_type": "sextortion_blackmail",
            "options": [
                {
                    "text": "Sharmanda bo'lmaslik uchun aytilgan pulni tezda to'layman.",
                    "is_correct": False,
                    "behavior": "Shantajga bo'ysunuvchi",
                    "explanation": "❌ Bu 99% holatda 'Fake Sextortion' xabari! Ular hech qanday videoni olmagan, shunchaki millionlab odamlarga qo'rqitish uchun ommaviy xat yuborgan."
                },
                {
                    "text": "Vahimaga tushmayman, xatni o'chiraman yoki ichki ishlar kiber-xavfsizlik bo'limiga ariza beraman.",
                    "is_correct": True,
                    "behavior": "Qo'rquvni yenggan qat'iyatli",
                    "explanation": "✅ A'lo! Agar pul to'lasangiz, shantajchilar sizni butun umr sog'ishga urinishadi. To'lamaslik va xabar berish eng to'g'ri yo'ldir."
                },
                {
                    "text": "Ular bilan gaplashib, videoni ko'rsatishni talab qilaman.",
                    "is_correct": False,
                    "behavior": "Muloqotga kirishuvchi",
                    "explanation": "⚠️ Firibgar bilan aloqaga kirishsangiz sizning qo'rqqaningizni bilib oladi."
                }
            ]
        },
        {
            "id": 609,
            "title": "Omma ta'siriga tushish (Social Proof / Hamma olyapti)",
            "scenario": "Guruhda 50 ta odam: 'Men falon botdan 2 million so'm oldim!', 'Rahmat sizlarga, menga ham pul tushdi!' deb cheklar rasmini tashlamoqda.",
            "question": "Hamma maqtayotgan bo'lsa, demak bu haqiqatmi?",
            "behavior_type": "social_proof_manipulation",
            "options": [
                {
                    "text": "Shuncha odam aldamaydi-ku, men ham qatnashaman.",
                    "is_correct": False,
                    "behavior": "Ommaga ko'r-ko'rona ergashuvchi",
                    "explanation": "❌ Bu 'Feyk botlar' to'dasi! Guruhdagi 50 ta profilning barchasi bitta firibgarga tegishli soxta hisoblardir."
                },
                {
                    "text": "Bu sahnalashtirilgan o'yin ekanini bilaman, ommaviy maqtovlarga aldanmayman.",
                    "is_correct": True,
                    "behavior": "Mustaqil tanqidiy fikrlovchi",
                    "explanation": "✅ Barakalla! Firibgarlar doimo sun'iy olomon effektidan (Social Proof) foydalanadi."
                },
                {
                    "text": "O'sha odamlarning biriga yozib, rostmi deb so'rayman.",
                    "is_correct": False,
                    "behavior": "Soxta profilga ishonuvchi",
                    "explanation": "❌ O'sha profil ham firibgarning o'zi bo'ladi va 'Ha, rost' deb tasdiqlaydi."
                }
            ]
        },
        {
            "id": 610,
            "title": "Ishonch qozonish uchun kichik foyda berish",
            "scenario": "Bir loyihaga 50,000 so'm tikdingiz, sizga 100,000 so'm qilib qaytarib berishdi. Endi ular: 'Katta yutuq uchun 5,000,000 so'm tiking' deyishyapti.",
            "question": "Katta pulni tikasizmi?",
            "behavior_type": "bait_and_switch",
            "options": [
                {
                    "text": "Ha, birinchi safar to'lab berishdi-ku, demak ishonchli.",
                    "is_correct": False,
                    "behavior": "Qarmakka ilingan baliq",
                    "explanation": "❌ Bu eng qadimgi tuzoq (Qarmak)! Kichik pul sizning ishonchingizni qozonish uchun berilgan jem edi. Katta pulni berishingiz bilan g'oyib bo'lishadi."
                },
                {
                    "text": "Yo'q! Bu tuzoq ekanligini tushunaman va darhol to'xtayman.",
                    "is_correct": True,
                    "behavior": "Strategik aql egasi",
                    "explanation": "✅ Qoyilmaqom! Firibgarlar katta o'lja uchun kichik mablag'ni sarflashdan qo'rqmaydi."
                },
                {
                    "text": "Do'stlarimdan qarz olib 10 million tikaman.",
                    "is_correct": False,
                    "behavior": "O'ta xavfli qimorboz",
                    "explanation": "❌ Butunlay xonavayron bo'lish yo'li."
                }
            ]
        }
    ],

    # -------------------------------------------------------------
    # LEVEL 7: Soxta Ish, Investitsiya va Kripto Piramidalar (10 ta savol)
    # -------------------------------------------------------------
    7: [
        {
            "id": 701,
            "title": "YouTube yoki TikTokda layk bosib pul ishlash",
            "scenario": "Sizga Telegramda xabar keldi: 'Amazon/Wildberries uchun kuniga 10 ta videoga layk bosing va kuniga 400,000 so'm maosh oling. Boshlash uchun VIP hisob sotib oling'.",
            "question": "Bunday ish taklifiga ishonasizmi?",
            "behavior_type": "task_scam",
            "options": [
                {
                    "text": "Oson ish ekan, ozgina pul to'lab VIP hisob olib boshlayman.",
                    "is_correct": False,
                    "behavior": "Tekin boylikka ishonuvchi (Task Scam qurboni)",
                    "explanation": "❌ Bu 'Task Scam' deb nomlanadi! Hech kim oddiy layk uchun 400 ming to'lamaydi. VIP hisob uchun bergan pulingiz firibgarga ketadi."
                },
                {
                    "text": "Haqiqiy ish beruvchi xodimdan pul so'ramaydi — bu firibgarlik deb rad etaman.",
                    "is_correct": True,
                    "behavior": "Mehnat bozorini tushunuvchi",
                    "explanation": "✅ To'g'ri! Ishga kirish uchun xodimdan pul talab qilinishi — 100% firibgarlik belgisidir."
                },
                {
                    "text": "Bir hafta ishlab, pulini keyin berasan deyman.",
                    "is_correct": False,
                    "behavior": "Soddadil savdolashuvchi",
                    "explanation": "⚠️ Ular baribir sizni har xil to'lovlar bilan aldashga urinadi."
                }
            ]
        },
        {
            "id": 702,
            "title": "Kafolatlangan kunlik 5% foyda (Piramida / Ponzi)",
            "scenario": "'Falon Invest' kompaniyasi sizga: 'Bizning neft yoki sun'iy intellekt fondimizga pul tiking, har kuni kafolatlangan 5% daromad olasiz!' demoqda.",
            "question": "Kafolatlangan kunlik 5% foyda realmi?",
            "behavior_type": "ponzi_scheme_awareness",
            "options": [
                {
                    "text": "Ha, zamonaviy texnologiyalar shunaqa katta foyda berishi mumkin.",
                    "is_correct": False,
                    "behavior": "Moliyaviy illyuziyaga ishonuvchi",
                    "explanation": "❌ Dunyoda hech qanday qonuniy biznes kunlik 5% (yiliga 1800%!) kafolatlangan foyda bera olmaydi. Bu oddiy Ponzi moliyaviy piramidasi!"
                },
                {
                    "text": "Yo'q, bu aniq moliyaviy piramida. Yangi odamlar puli evaziga ozroq ishlab, keyin butunlay yopilib qochadi.",
                    "is_correct": True,
                    "behavior": "Moliyaviy savodxon",
                    "explanation": "✅ A'lo! Haddan tashqari yuqori va kafolatlangan foyda — moliyaviy piramidaning 1-raqamli tamg'asidir."
                },
                {
                    "text": "Boshida ozgina tikib, foydasi bilan tezda chiqib ketishga ulguraman.",
                    "is_correct": False,
                    "behavior": "Xavfli qimorboz",
                    "explanation": "❌ Piramidalar qachon yopilishini faqat egasi biladi, pulingizni olib chiqishga ulgurmaysiz."
                }
            ]
        },
        {
            "id": 703,
            "title": "Mashhurlar nomidan soxta investitsiya (Deepfake video)",
            "scenario": "Videoda taniqli shaxs yoki prezident: 'Har bir o'zbekistonlik uchun gaz loyihasiga pul tikib oyiga 15 million daromad olish imkoniyati yaratildi' deb gapirmoqda. Tagida ro'yxatdan o'tish havolasi.",
            "question": "Bu loyihaga pul tikasizmi?",
            "behavior_type": "deepfake_investment_scam",
            "options": [
                {
                    "text": "Prezident yoki mashhur shaxs gapirayotgan bo'lsa, demak davlat kafolatlaydi.",
                    "is_correct": False,
                    "behavior": "Soxta videoga chuv tushuvchi",
                    "explanation": "❌ Bu Deepfake (AI orqali yuz va ovozni soxtalashtirish) orqali yasalgan soxta video! Davlat bunday investitsiya fondlarini targ'ib qilmaydi."
                },
                {
                    "text": "Bu soxta montaj va video-fishing. Havolaga kirmayman va boshqalarni ogohlantiraman.",
                    "is_correct": True,
                    "behavior": "Texnologik feyklarni ajrata oluvchi",
                    "explanation": "✅ Barakalla! Hozirda neft-gaz loyihalari niqobi ostida minglab odamlarni aldashmoqda."
                },
                {
                    "text": "Kamroq pul tikib, natijasini kutaman.",
                    "is_correct": False,
                    "behavior": "Tavakkalchi",
                    "explanation": "❌ Pul to'g'ridan-to'g'ri firibgarlarning cho'ntagiga tushadi."
                }
            ]
        },
        {
            "id": 704,
            "title": "Kriptovalyuta 'Signallar' kanali",
            "scenario": "Kripto-treyder kanali: 'Bizning VIP guruhga qo'shiling, 100 dollaringizni 1 kunda 2000 dollar qilib beramiz' deb va'da qilmoqda.",
            "question": "Pulingizni ularga boshqaruvga berasizmi?",
            "behavior_type": "crypto_pump_dump",
            "options": [
                {
                    "text": "Ha, o'zim tushunmayman, mutaxassis ko'paytirib bersa zo'r-ku.",
                    "is_correct": False,
                    "behavior": "Birovga mol-mulkini topshiruvchi",
                    "explanation": "❌ Pulingizni olgach, 'treyding o'xshamadi, hammasi kuyib ketdi' deyishadi yoki sizni kanaldan bloklashadi."
                },
                {
                    "text": "Kriptovalyutada hech kim 1 kunda 20 barobar daromadni kafolatlay olmaydi, bu firibgarlik.",
                    "is_correct": True,
                    "behavior": "Kripto bozorini tushunuvchi",
                    "explanation": "✅ To'g'ri! Haqiqiy treyderlar birovning pulini shubhali kanallarda yig'maydi."
                },
                {
                    "text": "Pasport nusxasini so'rab, keyin pul beraman.",
                    "is_correct": False,
                    "behavior": "Soxta hujjatga ishonuvchi",
                    "explanation": "❌ Ular internetdan topilgan soxta pasport rasmini yuborishadi."
                }
            ]
        },
        {
            "id": 705,
            "title": "Soxta birja (Broker) platformasi",
            "scenario": "Siz internetdagi bir platformaga 100$ kiritdingiz. Ekrandagi chiroyli grafiklarda pulingiz 1,000$ bo'lib ko'rinmoqda. Ammo pulni yechib olmoqchi bo'lsangiz: 'Yechish uchun yana 200$ komissiya to'lang' deyishyapti.",
            "question": "Komissiyani to'laysizmi?",
            "behavior_type": "advance_fee_broker",
            "options": [
                {
                    "text": "1000$ ni olish uchun 200$ to'lash arziydi, to'layman.",
                    "is_correct": False,
                    "behavior": "Cho'kayotganda xaskashga yopishuvchi",
                    "explanation": "❌ Qo'shimcha to'lagan 200$ pulingiz ham ketadi! Ekranda ko'ringan 1,000$ bu shunchaki qalbaki sonlar, u yerda hech qanday real pul yo'q."
                },
                {
                    "text": "Hech qanday qo'shimcha to'lov qilmayman — bu soxta brokerlik tuzog'i.",
                    "is_correct": True,
                    "behavior": "Yo'qotishni vaqtida to'xtatuvchi",
                    "explanation": "✅ A'lo! Qonuniy birjalar komissiyani yechilayotgan pulning o'zidan ushlab qoladi, tashqaridan to'lov so'ramaydi."
                },
                {
                    "text": "Ular bilan sudlashaman deb qo'rqitaman.",
                    "is_correct": False,
                    "behavior": "Hissiyotga beriluvchi",
                    "explanation": "⚠️ Ular noma'lum ofshor zonalarda joylashgan bo'lib, tahdiddan qo'rqmaydi."
                }
            ]
        },
        {
            "id": 706,
            "title": "Onlayn vakansiya uchun 'Oldindan to'lov'",
            "scenario": "Xorijiy kompaniyaga masofaviy ishga qabul qilindingiz. Ular: 'Sizga noutbuk va jihozlar jo'natamiz, lekin yetkazib berish va hujjatlar uchun 50$ to'lang' deyishdi.",
            "question": "Haqiqiy ish beruvchi yetkazib berish uchun pul so'raydimi?",
            "behavior_type": "employment_fraud",
            "options": [
                {
                    "text": "Ha, xorijdan noutbuk kelsa 50$ arziydi.",
                    "is_correct": False,
                    "behavior": "Ish ilinjida aldanuvchi",
                    "explanation": "❌ Bu 'Employment Scam'! Haqiqiy nufuzli kompaniyalar jihozlarni o'z hisobidan jo'natadi, nomzoddan bir tiyin ham so'ramaydi."
                },
                {
                    "text": "Yo'q, bu ish qidirayotganlarni aldovchi firibgarlik usuli.",
                    "is_correct": True,
                    "behavior": "Karyera xavfsizligini biluvchi",
                    "explanation": "✅ To'g'ri! Ishga kirishda oldindan to'lov so'raldimi — demak ish yo'q."
                },
                {
                    "text": "Oyligimdan ushlab qoling deb aytaman.",
                    "is_correct": False,
                    "behavior": "Murosa qiluvchi",
                    "explanation": "❌ Ular rozi bo'lmaydi, chunki maqsad sizdan naqd pul olish."
                }
            ]
        },
        {
            "id": 707,
            "title": "Piramidaga do'stlarni chaqirish (Referral bosimi)",
            "scenario": "Bir loyihaga kirdingiz. Sizga: 'Pulingizni chiqarib olishingiz uchun kamida 3 ta do'stingizni olib kelishingiz va ularga ham pul tiktirishingiz kerak' deyildi.",
            "question": "Do'stlaringizni chaqirasizmi?",
            "behavior_type": "pyramid_recruitment_ethics",
            "options": [
                {
                    "text": "O'z pulimni chiqarish uchun do'stlarimni aldab bo'lsa ham chaqiraman.",
                    "is_correct": False,
                    "behavior": "Boshqalarni qurbon qiluvchi",
                    "explanation": "❌ Siz ham firibgarlik sherigiga aylanasiz va yaqinlaringiz oldida obro'ingizni yo'qotasiz."
                },
                {
                    "text": "Aslo yo'q! Bu moliyaviy piramidaning eng iflos usuli. Yaqinlarimni xavf ostiga qo'ymayman.",
                    "is_correct": True,
                    "behavior": "Prinsipial va vijdonli",
                    "explanation": "✅ Barakalla! Haqiqiy investitsiya yangi odam olib kelishga majburlamaydi."
                },
                {
                    "text": "Notanish odamlarga spam tarqataman.",
                    "is_correct": False,
                    "behavior": "Spamchi",
                    "explanation": "❌ Bu ham boshqalarga zarar yetkazadi."
                }
            ]
        },
        {
            "id": 708,
            "title": "Telegram orqali Kripto AirDrop tuzog'i",
            "scenario": "Telegram bot: 'Bizning yangi koinimiz chiqdi, hamyoningizni (TrustWallet/Tonkeeper) ulang va 500$ lik tekin token oling' dedi. Hamyonni ulashda 'Seed phrase' (12 ta maxfiy so'z)ni kiritishni so'radi.",
            "question": "12 ta maxfiy so'zni kiritasizmi?",
            "behavior_type": "crypto_seed_phrase",
            "options": [
                {
                    "text": "Koinlarni qabul qilish uchun so'zlarni kiritaman.",
                    "is_correct": False,
                    "behavior": "Kripto savodsiz",
                    "explanation": "❌ 12 ta so'z — bu hamyoningizning bosh kalitidir! Uni kiritishingiz bilan ichidagi barcha kriptovalyutalar o'sha soniyadayoq o'g'irlanadi."
                },
                {
                    "text": "Hech qachon va hech qanday sharoitda 12 ta maxfiy so'zni hech kimga bermaslik kerak!",
                    "is_correct": True,
                    "behavior": "Kripto-xavfsizlik qoidalarini puxta biluvchi",
                    "explanation": "✅ Mukammal! Seed-fraza hech qachon hech qanday AirDrop yoki saytga kiritilmaydi."
                },
                {
                    "text": "Faqat 6 tasini kiritaman.",
                    "is_correct": False,
                    "behavior": "Chala xavfsizlik",
                    "explanation": "❌ Bu ham xato yondashuv."
                }
            ]
        },
        {
            "id": 709,
            "title": "Kripto P2P savdoda firibgarlik (Uchburchak sxemasi)",
            "scenario": "P2P orqali USDT sotmoqchisiz. Xaridor pulni begona odam nomidagi kartadan tashladi va 'Kriptoni tezda qo'yib yuboring' deb bosim qildi.",
            "question": "Tranzaksiyani tasdiqlab, USDT ni qo'yib yuborasizmi?",
            "behavior_type": "p2p_third_party_scam",
            "options": [
                {
                    "text": "Pul tushgan bo'lsa bo'ldi, kimning kartasidan tushgani muhim emas.",
                    "is_correct": False,
                    "behavior": "Uchburchak tuzog'iga tushuvchi",
                    "explanation": "❌ Bu 'Uchburchak' firibgarligi! Pul jabrlanuvchidan tushgan bo'lib, uning arizasi bilan kartangiz bloklanadi va firibgar kriptoni olib qochadi."
                },
                {
                    "text": "Uchinchi shaxs to'lovini qabul qilmayman — to'lovchi ismi birjadagi xaridor ismi bilan 100% bir xil bo'lishi shart.",
                    "is_correct": True,
                    "behavior": "P2P savdo qoidalariga qat'iy rioya qiluvchi",
                    "explanation": "✅ Qoyilmaqom! P2P da 3-shaxs to'lovlarini qabul qilish kartaning bloklanishiga olib keladi."
                },
                {
                    "text": "Pulni qaytarib, o'sha xaridorga boshqa joydan sotaman.",
                    "is_correct": False,
                    "behavior": "Beparvo",
                    "explanation": "⚠️ Birja ichidagi apellyatsiya orqali masalani hal qilish kerak."
                }
            ]
        },
        {
            "id": 710,
            "title": "Litsenziyasiz investitsiya kompaniyalari",
            "scenario": "Sizga investitsiya taklif qilayotgan kompaniyadan O'zbekiston Respublikasi Istiqbolli loyihalar milliy agentligi (NAPP) yoki Markaziy Bank litsenziyasini so'radingiz. Ular: 'Biz xalqaro London litsenziyasiga egamiz, O'zbekiston litsenziyasi shart emas' deyishdi.",
            "question": "Ushbu kompaniyaga pul ishonib bo'ladimi?",
            "behavior_type": "regulatory_compliance",
            "options": [
                {
                    "text": "London litsenziyasi bo'lsa yanada nufuzliroq ekan, ishonaman.",
                    "is_correct": False,
                    "behavior": "Qonuniy himoyasiz qoluvchi",
                    "explanation": "❌ Agar O'zbekiston litsenziyasi bo'lmasa, pulingiz o'g'irlanganda O'zbekiston qonunlari va sudi sizni himoya qila olmaydi!"
                },
                {
                    "text": "O'zbekistonda rasmiy ro'yxatdan o'tmagan va litsenziyasi bo'lmagan fondlarga pul tikish o'ta xavfli.",
                    "is_correct": True,
                    "behavior": "Qonuniy kafolatlarga tayangan investor",
                    "explanation": "✅ To'g'ri! Faqat milliy regulyator tomonidan nazorat qilinadigan platformalar xavfsizdir."
                },
                {
                    "text": "Internetdagi maqtovli sharhlarga qarab qaror qilaman.",
                    "is_correct": False,
                    "behavior": "Sharhlarga ishonuvchi",
                    "explanation": "❌ Sharhlarni pulga sotib olish mumkin."
                }
            ]
        }
    ],

    # -------------------------------------------------------------
    # LEVEL 8: Deepfake va Sun'iy Intellekt Firibgarligi (10 ta savol)
    # -------------------------------------------------------------
    8: [
        {
            "id": 801,
            "title": "AI orqali ovoz klonlash (Voice Cloning Scam)",
            "scenario": "Telefoningiz jiringladi. Do'stingiz yoki yaqin ukangizning aynan o'z ovozida: 'Aka, favqulodda holat bo'ldi, bitta kartaga 1 million tashlab yuboring, hozir gaplasholmayman' deb go'shakni qo'yib qo'ydi.",
            "question": "Sun'iy intellekt orqali ovozni 3 soniyali audio asosida 100% o'xshatib klonlash mumkinmi?",
            "behavior_type": "ai_voice_awareness",
            "options": [
                {
                    "text": "Yo'q, inson ovozini bunchalik aniq taqlid qilib bo'lmaydi, demak rostdan ham ukam.",
                    "is_correct": False,
                    "behavior": "AI imkoniyatlaridan bexabar",
                    "explanation": "❌ Bugungi AI modellari (ElevenLabs va b.) insonning bitta ovozli xabaridan foydalanib, uning ovozini 100% klonlay oladi!"
                },
                {
                    "text": "Ha! Bu AI ovoz klonlashi bo'lishi mumkin. Pul jo'natishdan oldin ukamga qayta qo'ng'iroq qilib, faqat ikkalamiz biladigan maxfiy savolni so'rayman.",
                    "is_correct": True,
                    "behavior": "Eng zamonaviy tahdidlarga tayyor",
                    "explanation": "✅ A'lo daraja! Oila ichida maxfiy 'Parol-so'z' (Safe word) joriy qilish AI ovoz klonlashiga qarshi yagona qalqondir."
                },
                {
                    "text": "Telegramdan: 'Ovozing boshqachami?' deb so'rayman.",
                    "is_correct": False,
                    "behavior": "Samarasiz tekshiruv",
                    "explanation": "⚠️ Shaxsiy muloqot va maxfiy savol orqali tekshirish kerak."
                }
            ]
        },
        {
            "id": 802,
            "title": "Videoqo'ng'iroqdagi AI Deepfake (Yuz almashtirish)",
            "scenario": "Telegram orqali rahbaringiz yoki tanishingiz videoqo'ng'iroq qildi. Ekranda uning yuzi ko'rinyapti, lekin lab harakati g'alati, ko'zlarini kam pirpiratmoqda va chetlarida xiralik bor.",
            "question": "Videoqo'ng'iroqda odamning yuzini jonli ravishda soxtalashtirish mumkinmi?",
            "behavior_type": "video_deepfake_recognition",
            "options": [
                {
                    "text": "Jonli video qo'ng'iroqda yuzni soxtalashtirish imkonsiz, bu haqiqiy odam.",
                    "is_correct": False,
                    "behavior": "Vizual texnologiyaga ko'r-ko'rona ishonuvchi",
                    "explanation": "❌ Real-time Deepfake dasturlari jonli videoqo'ng'iroqda ham yuzni boshqa odamga almashtirib bera oladi."
                },
                {
                    "text": "Ha, bu jonli Deepfake bo'lishi mumkin. Suhbatdoshdan qo'lini yuzi oldidan o'tkazishni yoki yon tomonga qarashni so'rayman.",
                    "is_correct": True,
                    "behavior": "Deepfake artefaktlarini fosh qiluvchi",
                    "explanation": "✅ Qoyilmaqom kiber-taktika! Qo'l yuz oldidan o'tganda yoki tez burilganda AI algoritmi xatoga yo'l qo'yadi va yuz buzilib ketadi."
                },
                {
                    "text": "Kameramni o'chirib tomosha qilib o'tiraman.",
                    "is_correct": False,
                    "behavior": "Passiv tomoshabin",
                    "explanation": "⚠️ Xavfni aniqlash va shubhali talablarni bajarmaslik kerak."
                }
            ]
        },
        {
            "id": 803,
            "title": "AI tomonidan yozilgan o'ta savodli fishing xatlari",
            "scenario": "Ilgari firibgarlar xatlarida ko'p imlo xatolar bo'lardi. Endi esa ChatGPT kabi modellar orqali rasmiy uslubda, beg'ubor o'zbek tilida yozilgan rasmiy taklifnoma keldi.",
            "question": "Imlo xatolarining yo'qligi xatning haqiqiyligiga kafolat bo'ladimi?",
            "behavior_type": "llm_generated_text_detection",
            "options": [
                {
                    "text": "Ha, xatosiz yozilgan bo'lsa, demak rasmiy idoradan kelgan.",
                    "is_correct": False,
                    "behavior": "Eski qoliplar bilan fikrlovchi",
                    "explanation": "❌ Bugungi kunda AI modellar istalgan tilda mukammal va savodli fishing matnlarini yarata oladi."
                },
                {
                    "text": "Yo'q, matn uslubiga emas, jo'natuvchining elektron manzili va havolalariga qarash kerak.",
                    "is_correct": True,
                    "behavior": "Mohiyatga qarab baholovchi",
                    "explanation": "✅ To'g'ri! Imlo xatolari yo'qligi xavfsizlik belgisi emas."
                },
                {
                    "text": "AI yozgan matnlarni sezish oson, shuning uchun xavfsiz.",
                    "is_correct": False,
                    "behavior": "O'ziga ortiqcha baho beruvchi",
                    "explanation": "❌ Zamonaviy LLM matnlarini inson matnidan ajratish deyarli imkonsiz."
                }
            ]
        },
        {
            "id": 804,
            "title": "Oilaviy maxfiy parol (Family Safe Word)",
            "scenario": "AI ovoz klonlash xavfi kuchaygan davrda oilangiz bilan nima qilishni kelishib olasiz?",
            "question": "Eng samarali himoya chorasi nima?",
            "behavior_type": "family_cyber_protocol",
            "options": [
                {
                    "text": "Telefon orqali umuman gaplashmaslik kerak.",
                    "is_correct": False,
                    "behavior": "O'ta radikal va noqulay",
                    "explanation": "❌ Muloqotni to'xtatish shart emas, qoidani o'zgartirish kifoya."
                },
                {
                    "text": "Oila a'zolari bilan faqat o'zimiz biladigan, internetda hech qachon ishlatilmagan maxfiy so'z kelishib olamiz.",
                    "is_correct": True,
                    "behavior": "Strategik xavfsizlik yaratuvchi",
                    "explanation": "✅ A'lo! Favqulodda pul so'ralganda shu so'z so'raladi. AI buni bila olmaydi."
                },
                {
                    "text": "Faqat audio xabar orqali gaplashamiz.",
                    "is_correct": False,
                    "behavior": "Zaif chora",
                    "explanation": "❌ Audio xabarni ham AI bemalol generatsiya qila oladi."
                }
            ]
        },
        {
            "id": 805,
            "title": "Sun'iy intellekt botlariga shaxsiy sirlarni yuklash",
            "scenario": "ChatGPT yoki boshqa ommaviy AI botiga ishxonangizning maxfiy moliyaviy hisobotini yoki pasport rasmingizni tahlil qildirish uchun yukladingiz.",
            "question": "Bunday qilish xavfsizmi?",
            "behavior_type": "ai_data_privacy",
            "options": [
                {
                    "text": "Ha, sun'iy intellekt buni hech kimga aytmaydi.",
                    "is_correct": False,
                    "behavior": "AI arxitekturasini tushunmaydigan",
                    "explanation": "❌ Ommaviy AI xizmatlariga kiritilgan ma'lumotlar modelni qayta o'qitishda ishlatilishi va boshqa foydalanuvchilar javoblarida sizib chiqishi mumkin!"
                },
                {
                    "text": "Yo'q! Maxfiy, shaxsiy va korporativ ma'lumotlarni ommaviy AI xizmatlariga kiritish taqiqlanadi.",
                    "is_correct": True,
                    "behavior": "Ma'lumotlar daxlsizligini saqlovchi",
                    "explanation": "✅ To'g'ri! Korporativ maxfiylik va shaxsiy daxlsizlik AI xavfsizligining eng muhim qismidir."
                },
                {
                    "text": "Faqat ingliz tilida yuklasam hech kim tushunmaydi.",
                    "is_correct": False,
                    "behavior": "Soddadil",
                    "explanation": "❌ AI barcha tillarni mukammal tushunadi."
                }
            ]
        },
        {
            "id": 806,
            "title": "Soxta sud qarori yoki hujjat (AI-generated document)",
            "scenario": "Sizga rasmiy muhrlar, shtrix-kodlar va imzo bilan soxta sud qarori yuborildi. Barcha rekvizitlar go'yoki haqiqiydek ko'rinadi.",
            "question": "Hujjatning haqiqiyligini qanday tekshirasiz?",
            "behavior_type": "document_verification",
            "options": [
                {
                    "text": "Muhr va shtrix-kod bor ekan, demak rasmiy hujjat.",
                    "is_correct": False,
                    "behavior": "Vizual atributlarga aldanuvchi",
                    "explanation": "❌ AI grafik vositalari orqali istalgan muhr va rasmiy blankani 5 daqiqada yasash mumkin."
                },
                {
                    "text": "Sudning rasmiy portali (masalan, sud.uz) orqali ish raqamini kiritib, haqiqatda mavjudligini tekshiraman.",
                    "is_correct": True,
                    "behavior": "Reyestrlar orqali tekshiruvchi",
                    "explanation": "✅ Barakalla! Haqiqiy sud qarorlari doimo rasmiy davlat sud bazasida qayd etilgan bo'ladi."
                },
                {
                    "text": "Hujjatda ko'rsatilgan telefonga qo'ng'iroq qilaman.",
                    "is_correct": False,
                    "behavior": "Soxta kontaktga murojaat qiluvchi",
                    "explanation": "❌ Hujjatdagi telefon ham firibgarning sherigiga tegishli bo'ladi."
                }
            ]
        },
        {
            "id": 807,
            "title": "Klonlangan ijtimoiy tarmoq profili (Avatar & Bio)",
            "scenario": "Do'stingizning profili xuddi o'zidek ochilgan — barcha rasmlari, postlari va do'stlar ro'yxati bir xil. U sizga qayta do'stlik tashlab, shaxsiy savol beryapti.",
            "question": "Bu vaziyatni nima deb atashadi?",
            "behavior_type": "profile_cloning",
            "options": [
                {
                    "text": "Do'stim yangi profil ochibdi, xursand bo'lib qo'shib olaman.",
                    "is_correct": False,
                    "behavior": "Identifikatsiya qilmaydigan",
                    "explanation": "❌ Bu 'Profil klonlash' hujumi! Firibgar ochiq profildan barcha ma'lumotlarni ko'chirib, uning nomidan aldovni amalga oshiradi."
                },
                {
                    "text": "Do'stimning eski profili yoki telefoni orqali bog'lanib, yangi profil ochgan-ochmaganini aniqlayman.",
                    "is_correct": True,
                    "behavior": "Klonni fosh qiluvchi",
                    "explanation": "✅ To'g'ri! Ikkilamchi kanallar orqali tekshirish klonlangan profillarni bir zumda fosh qiladi."
                },
                {
                    "text": "Eski profilini o'chirib tashlayman.",
                    "is_correct": False,
                    "behavior": "Mantiqsiz harakat",
                    "explanation": "⚠️ Siz eski haqiqiy do'stingizni o'chirib qo'yishingiz mumkin."
                }
            ]
        },
        {
            "id": 808,
            "title": "Avtomatlashtirilgan AI qo'ng'iroqlar botlari (AI Robocalls)",
            "scenario": "Sizga telefon qilishdi, go'shak ortidagi 'operator' sizning savollaringizga real vaqtda juda chiroyli javob beryapti, lekin oraliq pauzalarda 1 soniyali g'alati sukunat bor.",
            "question": "Siz bilan kim gaplashmoqda?",
            "behavior_type": "conversational_ai_robocall",
            "options": [
                {
                    "text": "Haqiqiy jonli odam bilan gaplashyapman.",
                    "is_correct": False,
                    "behavior": "Sun'iy intellektni payqamaydigan",
                    "explanation": "❌ Bu zamonaviy ovozli AI agenti (LLM Voice Agent)! Ular minglab odamlarga bir vaqtda qo'ng'iroq qilib, ma'lumot yig'ishga qodir."
                },
                {
                    "text": "Bu sun'iy intellekt ovozli boti bo'lishi mumkin. Mantiqsiz murakkab savol berib (masalan: 'Ot bilan filning qaysi biri muzqaymoq yeydi?') uning robotligini tekshiraman.",
                    "is_correct": True,
                    "behavior": "Tyuring testini qo'llovchi kiber-aqlli",
                    "explanation": "✅ Qoyilmaqom usul! Nostandart savollar AI botlarni dovdiratib qo'yadi."
                },
                {
                    "text": "U bilan 1 soat suhbatlashib o'tiraman.",
                    "is_correct": False,
                    "behavior": "Vaqtini yo'qotuvchi",
                    "explanation": "⚠️ Bot sizning ovoz namunangizni yozib olayotgan bo'lishi mumkin."
                }
            ]
        },
        {
            "id": 809,
            "title": "Telegram ovozli xabarlarini klonlash",
            "scenario": "Guruhdagi boshliqingiz yoki buxgalteringiz nomidan ovozli xabar (voice message) keldi: 'Falonchi, mana bu kartaga tezda to'lovni tasdiqlang'.",
            "question": "Faqat ovozli xabar asosida to'lov qilinadimi?",
            "behavior_type": "voice_payment_protocol",
            "options": [
                {
                    "text": "O'zining ovozi bilan aytdi-ku, darhol to'layman.",
                    "is_correct": False,
                    "behavior": "Ovozga so'zsiz ishonuvchi",
                    "explanation": "❌ Katta xato! Hozirda butun dunyoda ovozli xabar kloni orqali millionlab dollarlik korporativ o'g'riliklar bo'lmoqda."
                },
                {
                    "text": "Yo'q, moliyaviy to'lovlar hech qachon faqat ovozli xabar orqali amalga oshirilmaydi, rasmiy schyot-faktura va jonli tasdiq talab qilinadi.",
                    "is_correct": True,
                    "behavior": "Qat'iy korporativ protokol tarafdori",
                    "explanation": "✅ A'lo! Ovoz klonlanishi mumkin, ammo qat'iy buxgalteriya qoidalari buzilmasligi kerak."
                },
                {
                    "text": "Xabarni boshqa hamkasblarimga ham eshittirib ko'raman.",
                    "is_correct": False,
                    "behavior": "Vaqtni cho'zuvchi",
                    "explanation": "⚠️ Rasmiy tartibda rad etish kerak."
                }
            ]
        },
        {
            "id": 810,
            "title": "O'z ovozingiz va yuzingizni himoya qilish",
            "scenario": "Ijtimoiy tarmoqlarda ochiq profilda o'zingizning yuzingiz yaqindan olingan yuzlab videolaringiz va ovozingiz yozilgan podkastlar ochiq turibdi.",
            "question": "Firibgarlar bundan qanday foydalanishi mumkin?",
            "behavior_type": "biometric_data_exposure",
            "options": [
                {
                    "text": "Hech narsa qila olishmaydi, men mashhur emasman.",
                    "is_correct": False,
                    "behavior": "Xavfni o'ziga yaqinlashtirmaydigan",
                    "explanation": "❌ Firibgarlar aynan oddiy odamlarning materiallaridan ularning ota-onalari va qarindoshlarini aldashda foydalanadi."
                },
                {
                    "text": "Ushbu ma'lumotlar asosida mening AI klonimni yaratib, yaqinlarimdan pul undirishda ishlatishlari mumkin.",
                    "is_correct": True,
                    "behavior": "Biometrik xavflarni anglovchi",
                    "explanation": "✅ To'g'ri! Ijtimoiy tarmoqlarda yopiq profil (Private) saqlash va biometriyani himoyalash bugungi kun talabidir."
                },
                {
                    "text": "Faqat qorong'uda tushgan rasmlarni joylash kerak.",
                    "is_correct": False,
                    "behavior": "Yuzaki yechim",
                    "explanation": "⚠️ Profil xavfsizligi va maxfiylik sozlamalari muhimroq."
                }
            ]
        }
    ],

    # -------------------------------------------------------------
    # LEVEL 9: Korporativ va Ish Joyidagi Kiber-Hujumlar (10 ta savol)
    # -------------------------------------------------------------
    9: [
        {
            "id": 901,
            "title": "Soxta rahbar topshirig'i (CEO Fraud / BEC)",
            "scenario": "Ishxonangiz direktori nomidan favqulodda email yoki Telegram keldi: 'Men hozir yig'ilishdaman, gaplasholmayman. Zudlik bilan yangi hamkorimizning hisobiga 30 million so'm to'lovni o'tkazing, kechiksa shartnoma bekor bo'ladi!'.",
            "question": "Kompaniya hisobchisi sifatida nima qilasiz?",
            "behavior_type": "bec_fraud_defense",
            "options": [
                {
                    "text": "Direktorning jahli chiqmasligi uchun aytilgan to'lovni darhol bajaraman.",
                    "is_correct": False,
                    "behavior": "Bosim ostida protokolni buzuvchi",
                    "explanation": "❌ Bu dunyodagi eng qimmat firibgarlik — 'Business Email Compromise' (BEC)! Yiliga milliardlab dollar shunday o'g'irlanadi."
                },
                {
                    "text": "To'lovni to'xtatib turaman va rahbarning o'zi bilan yuzma-yuz yoki tasdiqlangan ichki aloqa kanali orqali gaplashmagunimcha pul o'tkazmayman.",
                    "is_correct": True,
                    "behavior": "Korporativ xavfsizlik ustuni",
                    "explanation": "✅ Qoyilmaqom! Boshliqning g'azabidan qo'rqish kompaniya xazinasini boy berishdan yaxshiroq emas."
                },
                {
                    "text": "Direktorning o'rinbosariga to'lataman.",
                    "is_correct": False,
                    "behavior": "Javobgarlikdan qochuvchi",
                    "explanation": "❌ Mas'uliyat baribir sizga yuklanadi."
                }
            ]
        },
        {
            "id": 902,
            "title": "Zararli hisob-faktura (Invoice.pdf.exe)",
            "scenario": "Hamkor kompaniyadan kutilmagan email keldi: 'O'tgan oylik xizmatlar uchun to'lov hisobi'. Biriktirilgan fayl nomi: 'Hisob_faktura_2026.pdf.exe'.",
            "question": "Faylni ochasizmi?",
            "behavior_type": "double_extension_awareness",
            "options": [
                {
                    "text": "Ha, PDF fayl ekan-ku, hisobni ko'rishim kerak.",
                    "is_correct": False,
                    "behavior": "Fayl kengaytmasini tushunmaydigan",
                    "explanation": "❌ Bu ikki karra kengaytma (Double Extension) hiylasi! Aslida fayl .exe (bajariluvchi dastur), ya'ni butun korporativ tarmoqni shifrlab qo'yuvchi Ransomware virusi!"
                },
                {
                    "text": "Aslo ochmayman! Bu .exe kengaytmali virus, darhol IT xavfsizlik bo'limiga xabar beraman.",
                    "is_correct": True,
                    "behavior": "Korporativ tarmoqni qutqaruvchi",
                    "explanation": "✅ A'lo! Haqiqiy hisob-fakturalar faqat .pdf bo'ladi, oxirida .exe yoki .scr bo'lmaydi."
                },
                {
                    "text": "Fleshkaga ko'chirib, uyda ochib ko'raman.",
                    "is_correct": False,
                    "behavior": "Xavfni uyiga eltuvchi",
                    "explanation": "❌ Uydagi kompyuteringiz ham zararlanadi."
                }
            ]
        },
        {
            "id": 903,
            "title": "Koridorda topib olingan noma'lum USB fleshka (BadUSB)",
            "scenario": "Ofis koridorida yoki avtoturargohda ustiga 'Oylik maoshlar va mukofotlar 2026' deb yozilgan yangi USB fleshka yotganini ko'rdingiz.",
            "question": "Fleshkani kompyuteringizga tiqib ko'rasizmi?",
            "behavior_type": "usb_drop_attack",
            "options": [
                {
                    "text": "Qiziq-ku, kim qancha oylik olayotganini bilish uchun kompyuterga tiqib ko'raman.",
                    "is_correct": False,
                    "behavior": "Qiziquvchanlik tuzog'iga tushuvchi (BadUSB qurboni)",
                    "explanation": "❌ Bu mashhur 'USB Drop Attack' usuli! Fleshka ichiga kiritilgan mikrosxema bir necha soniyada butun kompyuteringizni buzib kiradi."
                },
                {
                    "text": "Fleshkaga teginmayman yoki uni ochmasdan to'g'ridan-to'g'ri Kiber-xavfsizlik (IT) xizmatiga topshiraman.",
                    "is_correct": True,
                    "behavior": "Temir intizom egasi",
                    "explanation": "✅ To'g'ri! Noma'lum fleshkalarni xizmat kompyuteriga ulash mutlaqo taqiqlanadi."
                },
                {
                    "text": "Format qilib, o'zim uchun ishlataman.",
                    "is_correct": False,
                    "behavior": "Soddadil tejamkor",
                    "explanation": "❌ Formatlashgacha bo'lgan vaqtda ham virus ishga tushib ulguradi."
                }
            ]
        },
        {
            "id": 904,
            "title": "Parolni stikerga yozib monitorda qoldirish",
            "scenario": "Hamkasbingiz korporativ baza va pochtasining murakkab parolini unutmaslik uchun sariq qog'ozcha (stiker)ga yozib, monitorining burchagiga yopishtirib qo'ygan.",
            "question": "Bu xavfsizlikka to'g'ri keladimi?",
            "behavior_type": "clean_desk_policy",
            "options": [
                {
                    "text": "Ha, ofisda faqat o'zimizning xodimlar yuradi, hech narsa qilmaydi.",
                    "is_correct": False,
                    "behavior": "Ofis ichki xavflaridan bexabar",
                    "explanation": "❌ Tozalovchi xodimlar, kuryerlar, mijozlar yoki mehmonlar parolni ko'rib olib suratga tushirishi mumkin."
                },
                {
                    "text": "Yo'q! Bu 'Clean Desk Policy' (Toza stol qoidasi)ga ziddir. Parollar hech qachon ko'rinadigan joyda saqlanmaydi.",
                    "is_correct": True,
                    "behavior": "Korporativ standartlarga rioya qiluvchi",
                    "explanation": "✅ Barakalla! Parollarni faqat xavfsiz Parol menejerlarida saqlash lozim."
                },
                {
                    "text": "Klaviaturaning tagiga yashirib qo'yish kerak.",
                    "is_correct": False,
                    "behavior": "Kulgili himoya",
                    "explanation": "❌ Barcha firibgarlar eng birinchi klaviatura ostini tekshirishadi."
                }
            ]
        },
        {
            "id": 905,
            "title": "Eshikdan orqadan suqilib kirish (Tailgating / Piggybacking)",
            "scenario": "Kompaniyangiz eshigiga elektron kartochka (Turniket) o'rnatilgan. Siz kartangizni bosib kirayotganingizda orqangizdan qo'lida qutilar ko'targan notanish kishi: 'Iltimos, eshikni ushlab turing, qo'lim band' deb kirdi.",
            "question": "Uni ichkariga kiritasizmi?",
            "behavior_type": "physical_access_tailgating",
            "options": [
                {
                    "text": "Insoniylik yuzasidan eshikni ushlab turib o'tkazib yuboraman.",
                    "is_correct": False,
                    "behavior": "Jismoniy xavfsizlikni buzuvchi",
                    "explanation": "❌ Bu 'Tailgating' hujumi! Xakerlar qo'liga qutilar ko'tarib olib, korporativ binoga hech qanday ruxsatsiz kirib oladi."
                },
                {
                    "text": "Kechirasiz, qoidaga binoan har bir kishi o'z ruxsatnomasini alohida bosishi kerak, deb qo'riqchiga murojaat qilishini aytaman.",
                    "is_correct": True,
                    "behavior": "Qat'iy xavfsizlik nazoratchisi",
                    "explanation": "✅ Qoyil! Xavfsizlik qoidalari barcha uchun qat'iy va istisnosiz bo'lishi kerak."
                },
                {
                    "text": "Qutilarini ko'tarishga yordam beraman.",
                    "is_correct": False,
                    "behavior": "Chalg'uvchi",
                    "explanation": "⚠️ Bu orqali siz uning kirishini yanada osonlashtirasiz."
                }
            ]
        },
        {
            "id": 906,
            "title": "Korporativ pochtadan shaxsiy maqsadlarda foydalanish",
            "scenario": "Kompaniyangiz bergan 'ismingiz@kompaniya.uz' pochtangiz orqali shaxsiy o'yinlar, ijtimoiy tarmoqlar va onlayn do'konlardan ro'yxatdan o'tasizmi?",
            "question": "Bu xavfsizmi?",
            "behavior_type": "email_segregation",
            "options": [
                {
                    "text": "Ha, bitta pochtadan hamma joyda foydalangan qulay.",
                    "is_correct": False,
                    "behavior": "Chegaralarni aralashtirib yuboruvchi",
                    "explanation": "❌ Agar siz ro'yxatdan o'tgan qandaydir o'yin sayti buzilsa, sizning korporativ pochtangiz hakerlar bazasiga tushadi va korxona nishonga aylanadi."
                },
                {
                    "text": "Yo'q, korporativ pochta faqat xizmat faoliyati uchun, shaxsiy ishlar uchun shaxsiy Gmail bo'lishi kerak.",
                    "is_correct": True,
                    "behavior": "Kiber-gigiyenaga qat'iy amal qiluvchi",
                    "explanation": "✅ To'g'ri! Korporativ va shaxsiy raqamli hayot butunlay ajratilishi shart."
                },
                {
                    "text": "Faqat ishonchli do'konlarda ishlataman.",
                    "is_correct": False,
                    "behavior": "Yuzaki himoyachi",
                    "explanation": "❌ Har qanday yirik do'kon ham xakerlar hujumiga uchrashi mumkin."
                }
            ]
        },
        {
            "id": 907,
            "title": "Maxfiy hujjatlarni oddiy axlat qutisiga tashlash",
            "scenario": "Ofisda chop etilgan mijozlarning pasport nusxalari, shartnomalar va hisobotlar qoralamasini nima qilasiz?",
            "question": "Ularni qanday yo'q qilish to'g'ri?",
            "behavior_type": "dumpster_diving_defense",
            "options": [
                {
                    "text": "Shunchaki g'ijimlab, oddiy axlat paqiriga tashlayman.",
                    "is_correct": False,
                    "behavior": "Chiqindi xavfidan bexabar (Dumpster Diving qurboni)",
                    "explanation": "❌ 'Dumpster Diving' usuli orqali firibgarlar kompaniyalarning axlat qutilarini titib, yuzlab maxfiy hujjatlarni qo'lga kiritadi."
                },
                {
                    "text": "Faqat qog'oz maydalagich (Shredder) apparati orqali to'liq qirqib yo'q qilaman.",
                    "is_correct": True,
                    "behavior": "Axborot xavfsizligi intizomiga ega",
                    "explanation": "✅ A'lo! Qog'ozdagi maxfiy ma'lumotlar qayta tiklanmaydigan holatga keltirilishi shart."
                },
                {
                    "text": "Ustiga qora ruchka bilan chizib tashlayman.",
                    "is_correct": False,
                    "behavior": "Samarasiz himoya",
                    "explanation": "❌ Chiziqlar ostidagi yozuvni maxsus chiroq orqali bemalol o'qish mumkin."
                }
            ]
        },
        {
            "id": 908,
            "title": "Ish kompyuteriga shaxsiy noqonuniy o'yinlar o'rnatish",
            "scenario": "Tushlik vaqtida ishxona kompyuteriga torrentdan bepul o'g'irlangan (Torrent / Crack) o'yin yoki dastur o'rnatmoqchisiz.",
            "question": "Buning kompaniya tarmog'iga qanday zarari bor?",
            "behavior_type": "shadow_it_risk",
            "options": [
                {
                    "text": "Hech qanday zarari yo'q, o'ynab bo'lib o'chirib tashlayman.",
                    "is_correct": False,
                    "behavior": "Korporativ riskni tushunmaydigan",
                    "explanation": "❌ Crack qilingan o'yinlar 90% holatda yashirin backdoor troyanlar bilan ta'minlangan. Butun korxona serverlari shifrlanib qolishi mumkin."
                },
                {
                    "text": "Xizmat kompyuteriga ruxsat etilmagan dasturlarni o'rnatish butun tarmoqqa xavf tug'diradi, bu qat'iyan taqiqlanadi.",
                    "is_correct": True,
                    "behavior": "Kompaniya xavfsizligini o'zidek asrovchi",
                    "explanation": "✅ To'g'ri! Ish kompyuteri faqat tasdiqlangan litsenziyali dasturlar bilan ishlashi kerak."
                },
                {
                    "text": "Faqat antivirusni o'chirib turib o'rnataman.",
                    "is_correct": False,
                    "behavior": "Xavfga o'z qo'li bilan eshik ochuvchi",
                    "explanation": "❌ Bu virusga qasddan yo'l ochib berish demakdir."
                }
            ]
        },
        {
            "id": 909,
            "title": "Masofadan ishlash (VPN / Remote Work)",
            "scenario": "Uyda turib kompaniya ichki serverlariga ulanib ishlamoqchisiz.",
            "question": "Eng to'g'ri va xavfsiz ulanish usuli qaysi?",
            "behavior_type": "secure_remote_access",
            "options": [
                {
                    "text": "Oddiy internet orqali to'g'ridan-to'g'ri ochiq portga ulanaman.",
                    "is_correct": False,
                    "behavior": "Ochiq kanalga ishonuvchi",
                    "explanation": "❌ Ochiq portlar internetdagi skanerlar tomonidan darhol topiladi va buzib kiriladi."
                },
                {
                    "text": "Kompaniya tomonidan berilgan maxsus shifrlangan korporativ VPN va 2FA orqali ulanaman.",
                    "is_correct": True,
                    "behavior": "Tarmoq xavfsizligiga amal qiluvchi",
                    "explanation": "✅ Barakalla! Shifrlangan VPN tunnel ma'lumotlarni o'g'irlanishdan asraydi."
                },
                {
                    "text": "AnyDesk yoki TeamViewer orqali parolini ochiq qoldirib ulanaman.",
                    "is_correct": False,
                    "behavior": "Zaif ulanish tarafdori",
                    "explanation": "❌ Ochiq parolli masofaviy dasturlar xakerlar nishonidir."
                }
            ]
        },
        {
            "id": 910,
            "title": "Xodimning ishdan bo'shatilishida akkauntlarni yopish",
            "scenario": "Kompaniyada xodim ishdan bo'shadi. Uning elektron pochtasi va ichki bazaga kirish parollari 3 oy davomida o'chirilmay ochiq qoldi.",
            "question": "Buning xavfi nimada?",
            "behavior_type": "offboarding_security",
            "options": [
                {
                    "text": "Hech qanday xavfi yo'q, xodim yaxshi odam edi.",
                    "is_correct": False,
                    "behavior": "Insoniy omilga ortiqcha ishonuvchi",
                    "explanation": "❌ Sobiq xodim ma'lumotlarni raqobatchilarga sotishi yoki uning eskirgan akkaunti xakerlar uchun boshlang'ich nuqta bo'lishi mumkin."
                },
                {
                    "text": "Xodim bo'shashi bilanoq uning barcha korporativ hisoblari darhol bloklanishi (Offboarding) shart.",
                    "is_correct": True,
                    "behavior": "Protsessual intizomli",
                    "explanation": "✅ To'g'ri! O'z vaqtida o'chirilmagan 'Arvoh akkauntlar' (Orphan accounts) ko'plab kiber-hujumlarning sababchisidir."
                },
                {
                    "text": "Faqat parolini bitta raqamga o'zgartirib qo'yish kerak.",
                    "is_correct": False,
                    "behavior": "Chala yechim",
                    "explanation": "⚠️ Hisob to'liq yopilishi shart."
                }
            ]
        }
    ],

    # -------------------------------------------------------------
    # LEVEL 10: Ekstremal Kiber-Hujumlar va Kiber-Grossmeyster (10 ta savol)
    # -------------------------------------------------------------
    10: [
        {
            "id": 1001,
            "title": "SIM-Swap (SIM kartani dublikat qilish) hujumi",
            "scenario": "To'satdan telefoningizda tarmoq (aloqa) butunlay yo'qoldi: 'Faqat favqulodda qo'ng'iroqlar' (No Service). Bir necha daqiqadan so'ng do'stlaringiz siz nomingizdan g'alati xabarlar kelayotganini aytishdi.",
            "question": "Sizga nisbatan qanday murakkab hujum sodir bo'ldi va nima qilish kerak?",
            "behavior_type": "sim_swap_crisis",
            "options": [
                {
                    "text": "Telefonim buzilib qolibdi deb ustaxonaga olib boraman.",
                    "is_correct": False,
                    "behavior": "Texnik xatoga yo'yuvchi",
                    "explanation": "❌ Bu 'SIM-Swap' hujumi! Firibgar soxta ishonchnoma yoki aloqa kompaniyasidagi tanishi orqali sizning nomingizga yangi dublikat SIM-karta chiqartirib oldi. Sizning barcha SMS va qo'ng'iroqlaringiz unga ketyapti!"
                },
                {
                    "text": "Darhol boshqa telefondan mobil operatorga qo'ng'iroq qilib SIM-kartani zudlik bilan bloklataman va barcha banklarimni muzlataman.",
                    "is_correct": True,
                    "behavior": "Ekstremal vaziyatda grossmeyster",
                    "explanation": "✅ Qoyilmaqom kiber-grossmeyster javobi! SIM-Swap vaqtida har bir soniya g'animat. Operator orqali raqam darhol to'xtatilishi kerak."
                },
                {
                    "text": "Ertalabgacha kutaman, balki antena ta'mirlanayotgandir.",
                    "is_correct": False,
                    "behavior": "Halokatli kutuvchi",
                    "explanation": "❌ Ertalabgacha barcha bank hisoblaringiz va Telegramingiz qo'ldan ketadi."
                }
            ]
        },
        {
            "id": 1002,
            "title": "QR-ishing (Quishing / Soxta QR kodlar)",
            "scenario": "Mashinangiz oynasida yoki to'xtash joyidagi (parkovka) to'lov terminalida yangi stiker yopishtirilgan: 'Tezkor to'lov uchun QR kodni skaner qiling'.",
            "question": "Ko'chadagi QR kodlarga ko'r-ko'rona ishonish mumkinmi?",
            "behavior_type": "quishing_defense",
            "options": [
                {
                    "text": "Ha, QR kod bu shunchaki qulay texnologiya, xavfsiz.",
                    "is_correct": False,
                    "behavior": "QR texnologiyasiga ko'r ishonuvchi",
                    "explanation": "❌ Bu 'Quishing' (QR-fishing)! Firibgarlar haqiqiy QR kodlar ustiga o'zlarining soxta fishing saytlariga olib boruvchi stikerlarini yopishtirib ketishadi."
                },
                {
                    "text": "QR kod skaner qilinganda ochilayotgan URL manzilini diqqat bilan tekshiraman, shubhali stikerlar orqali to'lov qilmayman.",
                    "is_correct": True,
                    "behavior": "Vizual kodlarni tekshiruvchi",
                    "explanation": "✅ To'g'ri! QR kod ichidagi manzilni tekshirmasdan to'lov yoki login qilish o'ta xavflidir."
                },
                {
                    "text": "Kamerani yopib skaner qilaman.",
                    "is_correct": False,
                    "behavior": "Mantiqsiz harakat",
                    "explanation": "❌ Bu hech qanday natija bermaydi."
                }
            ]
        },
        {
            "id": 1003,
            "title": "Session Hijacking (Telegram Tdata o'g'irlanishi)",
            "scenario": "Xakerlar kompyuteringizdan Telegram Desktop papkasidagi 'tdata' faylini o'g'irlab ketishdi.",
            "question": "Ular 2FA parolingizni bilmasdan ham hisobingizga kira oladimi?",
            "behavior_type": "session_stealer_mechanics",
            "options": [
                {
                    "text": "Yo'q, parolsiz va SMS-kodsiz kira olmaydi.",
                    "is_correct": False,
                    "behavior": "Sessiya tokenlari mohiyatini bilmaydigan",
                    "explanation": "❌ Afsuski kira oladi! 'tdata' bu allaqachon ochilgan faol sessiya kalitidir. Xaker uni o'z kompyuteriga qo'yishi bilan hech qanday parolsiz sizning hisobingizga kiradi."
                },
                {
                    "text": "Ha! Faol sessiya tokeni orqali parolsiz kirish mumkin. Buni oldini olish uchun kompyuterga zararli dastur tushirmaslik va sessiyalarni muntazam tugatish kerak.",
                    "is_correct": True,
                    "behavior": "Chuqur kiber-arxitektura biluvchisi",
                    "explanation": "✅ A'lo bilim! Sessiya o'g'irlanishi (InfoStealer) bugungi kundagi eng xavfli hujum turlaridan biridir."
                },
                {
                    "text": "Faqat Linuxda shunaqa bo'ladi, Windowsda bo'lmaydi.",
                    "is_correct": False,
                    "behavior": "Operatsion tizim adashuvi",
                    "explanation": "❌ Aksincha, aksariyat InfoStealerlar aynan Windows uchun yaratiladi."
                }
            ]
        },
        {
            "id": 1004,
            "title": "Man-in-the-Middle (O'rtadagi odam) va SSL Stripping",
            "scenario": "Mehmonxonadagi Wi-Fi ga ulandingiz. Saytlarga kirayotganingizda brauzer sertifikatda xatolik borligini aytdi, lekin sayt ochilaverdi.",
            "question": "Bu vaziyatda nima sodir bo'lmoqda?",
            "behavior_type": "mitm_attack_detection",
            "options": [
                {
                    "text": "Mehmonxona interneti yaxshi ishlamayapti, e'tibor bermayman.",
                    "is_correct": False,
                    "behavior": "Xavfli signallarni e'tiborsiz qoldiruvchi",
                    "explanation": "❌ Bu 'Man-in-the-Middle' (MitM) hujumi! Xaker router va sizning orangizda turib barcha shifrlangan trafigingizni ochib o'qimoqda."
                },
                {
                    "text": "Bu oraliq trafikni ushlash hujumi bo'lishi mumkin! Zudlik bilan ushbu Wi-Fi dan uzilaman va shaxsiy mobil internetimga o'taman.",
                    "is_correct": True,
                    "behavior": "Tarmoq xavfsizligi mutaxassisi",
                    "explanation": "✅ Barakalla! SSL sertifikat xatolari ochiq tarmoqlarda shifrlash buzilganining aniq alomatidir."
                },
                {
                    "text": "Faqat rasm ko'raman, matn yozmayman.",
                    "is_correct": False,
                    "behavior": "Chala tushunuvchi",
                    "explanation": "❌ Barcha cookie va sessiyalar o'g'irlanadi."
                }
            ]
        },
        {
            "id": 1005,
            "title": "Kriptografik zaxira nusxalar va Ransomware (Tovlamachi virus)",
            "scenario": "Kompaniyangizdagi barcha fayllar shifrlanib qoldi va qora ekranda: 'Fayllarni ochish uchun 5 Bitcoin to'lang' degan yozuv chiqdi.",
            "question": "Tovlamachilarga pul to'lash to'g'rimi?",
            "behavior_type": "ransomware_response",
            "options": [
                {
                    "text": "Fayllar juda muhim, iloj yo'q, pulni to'laymiz.",
                    "is_correct": False,
                    "behavior": "Kiber-terrorizmga homiylik qiluvchi",
                    "explanation": "❌ To'langan taqdirda ham 50% holatda ular kalitni bermaydi yoki qayta pul talab qiladi. Qonunan ham terroristik guruhlarga pul to'lash taqiqlanadi."
                },
                {
                    "text": "Pul to'lanmaydi! Xavfsizlik xizmatiga murojaat qilinadi va oflayn (sovuq) zaxira nusxalardan (Offline Backups) tizim qayta tiklanadi.",
                    "is_correct": True,
                    "behavior": "Kiber-xavfsizlik strategiyasi yetakchisi",
                    "explanation": "✅ Grossmeysterona javob! Ransomwaredan yagona najot — internetga ulanmagan mustaqil zaxira nusxalardir (3-2-1 zaxira qoidasi)."
                },
                {
                    "text": "Kompyuterni derazadan uloqtiramiz.",
                    "is_correct": False,
                    "behavior": "Vahimachi",
                    "explanation": "⚠️ Bu muammoni hal qilmaydi."
                }
            ]
        },
        {
            "id": 1006,
            "title": "Brauzer kengaytmalari (Extensions) orqali xakerlik",
            "scenario": "Chrome brauzeringizga 'Bepul VPN' yoki 'Video yuklovchi' kengaytma (Extension) o'rnatgansiz. 1 oydan so'ng u dasturchi tomonidan boshqa xakerlarga sotildi va yangilandi.",
            "question": "Brauzer kengaytmalari sizning parollaringizni o'g'irlashi mumkinmi?",
            "behavior_type": "browser_extension_threat",
            "options": [
                {
                    "text": "Yo'q, kengaytmalar faqat brauzer ichida kichik yordamchi vosita.",
                    "is_correct": False,
                    "behavior": "Kengaytma xavfini bilmaydigan",
                    "explanation": "❌ Kengaytmalar brauzerdagi har qanday sahifa kodi va ma'lumotlarini o'qish hamda o'zgartirish ruxsatiga ega. Ular to'g'ridan-to'g'ri klaviatura yozuvlarini o'g'irlaydi."
                },
                {
                    "text": "Ha! Zararli kengaytmalar har bir kiritilgan parol va kartani to'g'ridan-to'g'ri o'g'irlay oladi. Faqat rasmiy va minimal kengaytmalar ishlatish kerak.",
                    "is_correct": True,
                    "behavior": "Brauzer xavfsizligini ta'minlovchi",
                    "explanation": "✅ To'g'ri! Keraksiz va shubhali barcha kengaytmalarni o'chirib tashlash zarur."
                },
                {
                    "text": "Faqat yashirin (Incognito) rejimda ishlatsam xavfsiz.",
                    "is_correct": False,
                    "behavior": "Noto'g'ri ishonch",
                    "explanation": "❌ Incognito rejim virusli kengaytmalardan himoya qilmaydi."
                }
            ]
        },
        {
            "id": 1007,
            "title": "Aparat darajasidagi hujumlar (Hardware Keylogger)",
            "scenario": "Ofis kompyuteringiz klaviaturasi kabeli va tizim bloki (korpus) orasiga kichik notanish adapter ulab ketilganini ko'rdingiz.",
            "question": "Bu moslama nima bo'lishi mumkin?",
            "behavior_type": "hardware_keylogger_detection",
            "options": [
                {
                    "text": "Bu shunchaki signal kuchaytirgich bo'lsa kerak.",
                    "is_correct": False,
                    "behavior": "Jismoniy xavfni sezmaydigan",
                    "explanation": "❌ Bu 'Hardware Keylogger' — klaviaturada terilgan har bitta harf va parolni ichki xotirasiga yozib oluvchi xakerlik qurilmasi!"
                },
                {
                    "text": "Bu apparatli keylogger bo'lishi mumkin. Kompyuterni darhol tarmoqdan uzib, kiber-xavfsizlik bo'limiga xabar beraman.",
                    "is_correct": True,
                    "behavior": "Yuqori hushyorlik darajasi",
                    "explanation": "✅ Mukammal! Jismoniy kiber-josuslik vositalarini fosh qilish eng oliy hushyorlik belgisidir."
                },
                {
                    "text": "Uni sug'urib, cho'ntagimga solib qo'yaman.",
                    "is_correct": False,
                    "behavior": "Dalillarni yo'qotuvchi",
                    "explanation": "⚠️ Ekspertlar kelib tekshirishi uchun ashyoviy dalil sifatida qoldirilishi kerak."
                }
            ]
        },
        {
            "id": 1008,
            "title": "Zero-Day zaifliklari va favqulodda yangilanishlar",
            "scenario": "Yangiliklarda Apple yoki Android tizimida 'Nol kunlik' (Zero-Day) zaiflik aniqlangani va hakerlar hech qanday havolani bosmasdan ham (Zero-Click exploit) telefonni buzayotgani aytildi.",
            "question": "Foydalanuvchi sifatida bunday hujumdan qanday himoyalanish mumkin?",
            "behavior_type": "zero_day_patching",
            "options": [
                {
                    "text": "Bunaqa narsalardan himoyalanib bo'lmaydi, taqdirga tan berish kerak.",
                    "is_correct": False,
                    "behavior": "Fatalist",
                    "explanation": "❌ Himoyalanish mumkin! Ishlab chiqaruvchilar bunday zaifliklar uchun zudlik bilan 'Hotfix' yamoqlarini chiqaradi."
                },
                {
                    "text": "Ishlab chiqaruvchi chiqargan favqulodda xavfsizlik yangilanishini (Emergency Security Patch) o'sha daqiqadayoq o'rnatish kerak.",
                    "is_correct": True,
                    "behavior": "Kiber-gigiyenaning eng yuqori cho'qqisi",
                    "explanation": "✅ Barakalla! Zero-Day hujumlariga qarshi yagona vosita — yangilanishlarni kechiktirmasdan o'rnatishdir."
                },
                {
                    "text": "Telefonni samolyot rejimiga (Airplane mode) qo'yib 1 oy ishlatish kerak.",
                    "is_correct": False,
                    "behavior": "Samarasiz radikal",
                    "explanation": "⚠️ Yangilanish o'rnatish eng oqilona yechim."
                }
            ]
        },
        {
            "id": 1009,
            "title": "Raqamli Iz va OSINT (Ochiq manbalar orqali josuslik)",
            "scenario": "Siz ijtimoiy tarmoqlarda mashinangiz raqami, farzandingiz maktabi, uyingizning derazasidan ko'rinish va samolyot chiptangiz shtrix-kodini rasmga olib ulashasiz.",
            "question": "Hakerlar ushbu ma'lumotlar orqali nima qila oladi?",
            "behavior_type": "osint_oversharing",
            "options": [
                {
                    "text": "Hech narsa, bu oddiy rasmlar-ku.",
                    "is_correct": False,
                    "behavior": "Raqamli iz xavfini bilmaydigan",
                    "explanation": "❌ OSINT (Open Source Intelligence) orqali xakerlar sizning butun hayotiy jadvalingizni, yashash manzilingizni va parollaringiz xarakterini 100% hisoblab chiqadi."
                },
                {
                    "text": "Bu ma'lumotlar orqali menga qarshi maqsadli ijtimoiy muhandislik hujumi (Spear Phishing) va jismoniy o'g'rilik rejalashtirish mumkin.",
                    "is_correct": True,
                    "behavior": "Shaxsiy xavfsizlik strategisti",
                    "explanation": "✅ Qoyilmaqom! Raqamli izni (Digital Footprint) minimal saqlash — zamonaviy dunyoda o'zini va oilasini asrashning asosidir."
                },
                {
                    "text": "Faqat samolyot chiptasi xavfli, boshqalari xavfsiz.",
                    "is_correct": False,
                    "behavior": "Chala xavfsiz",
                    "explanation": "❌ Har bir detal xakerlar uchun jumboqning bir bo'lagidir."
                }
            ]
        },
        {
            "id": 1010,
            "title": "Kiber-Grossmeysterlik Xulosasi va Doimiy Hushyorlik",
            "scenario": "Siz ushbu testdagi barcha qoidalarni o'rganib chiqdingiz. Kiber-xavfsizlikda eng zaif bo'g'in nima deb hisoblaysiz?",
            "question": "Kiber-xavfsizlikning 1-raqamli haqiqati nima?",
            "behavior_type": "human_factor_ultimate_truth",
            "options": [
                {
                    "text": "Eng zaif bo'g'in — bu kompyuterlar va zaif dasturlardir.",
                    "is_correct": False,
                    "behavior": "Texnikaga ayb qo'yuvchi",
                    "explanation": "❌ Dunyodagi eng kuchli shifrlash ham inson omili oldida ojizdir."
                },
                {
                    "text": "Eng zaif bo'g'in — bu INSON OMILI (his-tuyg'ular, ishonuvchanlik, qo'rquv va shoshmashosharlik). Shuning uchun doimiy bilim va xotirjamlik eng kuchli qalqondir.",
                    "is_correct": True,
                    "behavior": "Oliy Kiber-Grossmeyster",
                    "explanation": "✅ TABRIKLAYMIZ! Siz kiber-xavfsizlikning eng buyuk sirini tushundingiz: Xakerlar kompyuterlarni emas, odamlarning hissiyotlarini buzib kiradi. O'z hissiyotlaringizni boshqara olsangiz, sizni hech qachon alday olishmaydi!"
                },
                {
                    "text": "Eng zaif bo'g'in — internet provayderlardir.",
                    "is_correct": False,
                    "behavior": "Asosiy mohiyatdan uzoq",
                    "explanation": "❌ Inson omili — barcha kiber-hujumlarning 95% sababchisidir."
                }
            ]
        }
    ]
}


def get_level_meta(level: int) -> Dict[str, Any]:
    """Daraja metama'lumotlarini olish."""
    return LEVELS_META.get(level, {
        "title": f"{level}-Daraja",
        "difficulty": "Noma'lum",
        "badge": "Foydalanuvchi",
        "desc": "Kiber-xavfsizlik testi."
    })


def get_level_questions(level: int, randomize: bool = True) -> List[Dict[str, Any]]:
    """
    Berilgan daraja uchun 10 ta savolni olish.
    Agar randomize=True bo'lsa, savollar va ularning javob variantlari tasodifiy aralashtiriladi.
    Shunda har safar foydalanuvchiga har xil tartibda taqdim etiladi!
    """
    raw_list = ALL_QUIZ_DATA.get(level, [])
    if not raw_list:
        return []

    # Chuqur nusxa olish
    import copy
    questions = copy.deepcopy(raw_list)

    if randomize:
        random.shuffle(questions)

    for q in questions:
        if randomize:
            random.shuffle(q["options"])

    return questions


def analyze_user_behavior(answers_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Foydalanuvchining testdagi xatti-harakatlari va psixologik portretini tahlil qilish.
    answers_history: [{"behavior_type": "...", "is_correct": True/False, "behavior": "..."}]
    """
    total = len(answers_history)
    if total == 0:
        return {"summary": "Tahlil uchun ma'lumot yetarli emas."}

    correct_count = sum(1 for a in answers_history if a.get("is_correct"))
    score_percent = int((correct_count / total) * 100)

    # Xato qilingan psixologik nuqtalar
    weaknesses = {}
    for a in answers_history:
        if not a.get("is_correct"):
            b_type = a.get("behavior_type", "general")
            weaknesses[b_type] = weaknesses.get(b_type, 0) + 1

    profile = []
    if weaknesses.get("urgency_manipulation") or weaknesses.get("panic_pressure") or weaknesses.get("fear_intimidation"):
        profile.append("⚡ <b>Shoshilinchlik va qo'rquv:</b> Siz bosim va tahdid ostida tez xato qilasiz. Firibgarlar aynan shu emotsiyadan foydalanadi.")

    if weaknesses.get("greed_trap") or weaknesses.get("freebie_greed") or weaknesses.get("task_scam"):
        profile.append("🎁 <b>Tekin daromad va yutuqlar:</b> 'Kafolatlangan katta foyda' yoki 'tekin bonus' va'dalari sizni chalg'itishi mumkin. Ehtiyot bo'ling.")

    if weaknesses.get("trust_exploit") or weaknesses.get("social_manipulation") or weaknesses.get("empathy_exploit"):
        profile.append("🤝 <b>Haddan ortiq ishonuvchanlik:</b> Tanish yoki notanish odamlarning iltimoslariga haddan tashqari tez ishonasiz. Shaxsiy chegaralarni mustahkamlang.")

    if weaknesses.get("curiosity_bait") or weaknesses.get("link_curiosity"):
        profile.append("🔍 <b>Qiziquvchanlik:</b> Shubhali havolalar yoki fayllarni ko'rish istagi kuchli. Qiziqishni xavfsizlik nazoratidan o'tkazish zarur.")

    if not profile:
        profile.append("🛡️ <b>Kuchli ruhiy barqarorlik:</b> Siz bosim, yolg'on va vasvasalarga berilmaydigan, tanqidiy aql bilan qaror qabul qiluvchi xotirjam insonsiz!")

    # Reyting unvoni
    if score_percent == 100:
        rank = "🏆 Oliy Kiber-Qalqon"
        rank_desc = "Mukammal natija! Firibgarlar sizni hech qanday usul bilan alday olmaydi."
    elif score_percent >= 80:
        rank = "🥇 Hushyor Himoyachi"
        rank_desc = "Juda yaxshi! Siz kiber-xavflarni yaxshi tushunasiz, nozik psixologik tuzoqlarda biroz e'tibor talab etiladi."
    elif score_percent >= 60:
        rank = "⚠️ O'rta Darajali Ehtiyotkor"
        rank_desc = "Qoniqarli, ammo murakkab ijtimoiy muhandislik hujumlarida aldanish xavfi mavjud."
    else:
        rank = "🚨 Yuqori Xavf Guruhida"
        rank_desc = "Diqqat! Kiber-savodxonlik va hissiy hushyorlikni zudlik bilan oshirish zarur."

    return {
        "score": correct_count,
        "total": total,
        "percent": score_percent,
        "rank": rank,
        "rank_desc": rank_desc,
        "psychological_profile": profile
    }
