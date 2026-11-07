import asyncio
import os
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.security_engine.url_analyzer import analyze_url_or_text
from backend.security_engine.apk_analyzer import analyze_file_security
from backend.security_engine.contract_analyzer import analyze_contract_file
from backend.security_engine.card_analyzer import analyze_card_number
from backend.database import init_db

async def run_tests():
    print("--- 1. Baza initsializatsiyasi ---")
    await init_db()
    print("✅ Ma'lumotlar bazasi (SQLite) muvaffaqiyatli ishga tushdi.")

    print("\n--- 2. URL & Fishing Dvigateli Tekshiruvi ---")
    # Test 1: Rasmiy sayt
    res1 = await analyze_url_or_text("https://click.uz")
    print(f"Click.uz -> Xavf: {res1['risk_score']}%, Hukm: {res1['verdict']} ({res1['verdict_uz']})")
    assert res1['verdict'] == 'safe', "click.uz xavfsiz bo'lishi kerak!"

    # Test 2: Typosquatting / Fishing
    res2 = await analyze_url_or_text("Tezda kiring! http://c1ick-bonus.xyz saytida 10,000,000 so'm yutib oldingiz!")
    print(f"c1ick-bonus.xyz -> Xavf: {res2['risk_score']}%, Hukm: {res2['verdict']} ({res2['verdict_uz']})")
    assert res2['risk_score'] >= 70, "c1ick-bonus.xyz yuqori xavfli bo'lishi kerak!"

    # Test 3: Yashirin obuna va avtospisanie (1 so'm to'lov)
    res3 = await analyze_url_or_text("1 so'm to'lab 3 kunlik sinov obunasini oling. So'ngra har oy 199 000 so'm avtospisanie bo'ladi.")
    print(f"Yashirin avtospisanie -> Xavf: {res3['risk_score']}%, Hukm: {res3['verdict']}")
    assert res3['risk_score'] >= 70, "Yashirin avtospisanie 70+ xavf ko'rsatishi shart!"

    # Test 4: Soxta yetkazib berish va 'Pulni qabul qilib oling'
    res4 = await analyze_url_or_text("Salom, OLX orqali tovaringizni sotib olmoqchiman. Pulni to'lab qo'ydim, kartangizga qabul qilib oling.")
    print(f"Soxta dostavka -> Xavf: {res4['risk_score']}%, Hukm: {res4['verdict']}")
    assert res4['risk_score'] >= 70, "Soxta dostavka xavfli bo'lishi shart!"

    # Test 5: Soxta kredit sug'urta badali
    res5 = await analyze_url_or_text("Kredit tasdiqlandi! 50 000 000 so'm olishingiz uchun 250 000 so'm sug'urta badalini to'lang.")
    print(f"Soxta kredit badali -> Xavf: {res5['risk_score']}%, Hukm: {res5['verdict']}")
    assert res5['risk_score'] >= 70, "Soxta kredit badali xavfli bo'lishi shart!"

    # Test 6: Wildberries topshiriqlari layk piramidasi
    res6 = await analyze_url_or_text("Wildberries topshiriqlarini bajaring va kuniga 450 000 so'm daromad oling. Skrinshot yuboring.")
    print(f"Wildberries layk piramidasi -> Xavf: {res6['risk_score']}%, Hukm: {res6['verdict']}")
    assert res6['risk_score'] >= 70, "Wildberries layk piramidasi xavfli bo'lishi shart!"

    print("\n--- 3. Bank Kartasi Tahlili Tekshiruvi ---")
    card_uz = analyze_card_number("8600020000000005")
    print(f"Uzcard Xalq Banki -> Xavf: {card_uz['risk_score']}%, Hukm: {card_uz['verdict']}")
    assert card_uz['verdict'] == 'safe', "Rasmiy Uzcard xavfsiz bo'lishi kerak!"

    card_foreign = analyze_card_number("2202201234567890")
    print(f"Xorijiy Mir karta -> Xavf: {card_foreign['risk_score']}%, Hukm: {card_foreign['verdict']}")
    assert card_foreign['is_foreign'] == True, "Xorijiy karta aniqlanishi shart!"

    print("\n--- 4. APK & Fayl Skaneri Tekshiruvi ---")
    fake_apk_bytes = b"PK\x03\x04" + b"android.permission.BIND_ACCESSIBILITY_SERVICE" + b"\x00" * 50 + b"android.permission.RECEIVE_SMS"
    res_apk = analyze_file_security("To'y taklifnomasi.pdf.apk", fake_apk_bytes)
    print(f"To'y taklifnomasi.pdf.apk -> Xavf: {res_apk['risk_score']}%, Hukm: {res_apk['verdict']} ({res_apk['verdict_uz']})")
    assert res_apk['risk_score'] >= 70, "Zararli APK troyan 70+ risk ko'rsatishi shart!"

    print("\n--- 5. Shartnoma Rentgeni (Legal X-Ray) Tekshiruvi ---")
    sample_predatory_contract = """
    KREDIT VA QARZ SHARTNOMASI № 402/24.
    3.1. Qarz oluvchi har bir kechiktirilgan kun uchun muddati o'tgan summa miqdoridan 0.5% penya to'laydi.
    5.2. Bank foiz stavkasi va oylik qo'shimcha komissiya to'lovlarini bir tomonlama tartibda o'zgartirishga haqli.
    7.3. Qarzdorlik vujudga kelganda mol-mulk sud qarorisiz akseptsiz undiruvga qaratiladi.
    8.1. Kredit summasidan 500 000 so'm qaytarilmaydigan sug'urta badali ushlab qolinadi.
    9.2. Muddatidan oldin to'lash uchun 3% jarima belgilanadi.
    """
    res_con = await analyze_contract_file("kredit_shartnoma.txt", sample_predatory_contract.encode('utf-8'))
    print(f"Shartnoma auditi -> Xavfsizlik ko'rsatkichi: {res_con['overall_safety_score']}/100, Hukm: {res_con['verdict']}")
    print(f"Topilgan xavfli moddalar soni: {len(res_con['dangerous_clauses'])}")
    print(f"Yashirin moliyaviy tuzoqlar: {res_con['financial_traps']}")
    assert len(res_con['dangerous_clauses']) >= 4, "Shartnomadagi tuzoqlar to'liq aniqlanishi shart!"

    print("\n🎉 BARCHA TEKSHIRUVLAR MUVAFFAQIYATLI O'TDI!")

if __name__ == "__main__":
    asyncio.run(run_tests())
