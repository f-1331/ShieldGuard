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

    # Test 3: Prezident nomidan soxta yordam
    res3 = await analyze_url_or_text("Prezident yordam puli tarqatilmoqda, SMS kodni tasdiqlang")
    print(f"Soxta yordam -> Xavf: {res3['risk_score']}%, Hukm: {res3['verdict']}")
    assert res3['risk_score'] >= 70, "SMS va Prezident yordam puli xavfli bo'lishi kerak!"

    print("\n--- 3. APK & Fayl Skaneri Tekshiruvi ---")
    # Test 4: Ikki qavatli xavfli kengaytma va ijtimoiy muhandislik
    fake_apk_bytes = b"PK\x03\x04" + b"android.permission.BIND_ACCESSIBILITY_SERVICE" + b"\x00" * 50 + b"android.permission.RECEIVE_SMS"
    res4 = analyze_file_security("To'y taklifnomasi.pdf.apk", fake_apk_bytes)
    print(f"To'y taklifnomasi.pdf.apk -> Xavf: {res4['risk_score']}%, Hukm: {res4['verdict']} ({res4['verdict_uz']})")
    assert res4['risk_score'] >= 70, "Zararli APK troyan 70+ risk ko'rsatishi shart!"

    print("\n--- 4. Shartnoma Rentgeni (Legal X-Ray) Tekshiruvi ---")
    sample_predatory_contract = """
    KREDIT VA QARZ SHARTNOMASI № 402/24.
    3.1. Qarz oluvchi har bir kechiktirilgan kun uchun muddati o'tgan summa miqdoridan 0.5% penya to'laydi.
    5.2. Bank foiz stavkasi va oylik qo'shimcha komissiya to'lovlarini bir tomonlama tartibda o'zgartirishga haqli.
    7.3. Qarzdorlik vujudga kelganda mol-mulk sud qarorisiz akseptsiz undiruvga qaratiladi.
    """
    res5 = await analyze_contract_file("kredit_shartnoma.txt", sample_predatory_contract.encode('utf-8'))
    print(f"Shartnoma auditi -> Xavfsizlik ko'rsatkichi: {res5['overall_safety_score']}/100, Hukm: {res5['verdict']}")
    print(f"Topilgan xavfli moddalar soni: {len(res5['dangerous_clauses'])}")
    print(f"Yashirin moliyaviy tuzoqlar: {res5['financial_traps']}")
    assert len(res5['dangerous_clauses']) >= 2, "Shartnomadagi tuzoqlar aniqlanishi shart!"

    print("\n🎉 BARCHA TEKSHIRUVLAR MUVAFFAQIYATLI O'TDI!")

if __name__ == "__main__":
    asyncio.run(run_tests())
