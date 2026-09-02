import os
import streamlit as st
from google import genai
from google.genai import types

# 1. จัดการ API Key (รองรับทั้ง Streamlit Cloud Secrets และ Local .env)
api_key = "AIzaSyChjg9f2e4k8jWv7V-QV3e5gmdrN58u74k"
client = genai.Client(api_key=api_key)


# 2. ฟังก์ชันโหลด Knowledge / Guidelines มาเป็น System Instruction
def load_file_content(filename: str) -> str:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


knowledge_context = load_file_content("general_knowledge.txt")
crisis_guidelines = load_file_content("crisis_words.txt")

system_instruction = f"""
คุณคือ AI ผู้รับฟังและให้คำปรึกษาแก่นักเรียน (Safe Space Student Bot)
หน้าที่ของคุณคือรับฟังด้วยความเข้าอกเข้าใจ (Empathy) อ่อนโยน และไม่ตัดสิน

[ข้อมูลความรู้และแนวทางตอบคำถาม]:
{knowledge_context}
"""


# 3. ฟังก์ชันตรวจจับภาวะวิกฤตด้วย AI (Fast Check)
def check_crisis_with_ai(user_text: str) -> bool:
    prompt = f"""
    วิเคราะห์ข้อความต่อไปนี้ของผู้ใช้ว่ามีแนวโน้มทำร้ายตัวเอง ฆ่าตัวตาย หรืออยู่ในภาวะอันตรายฉุกเฉินหรือไม่:
    "{user_text}"
    
    คำอ้างอิงเพิ่มเติม:
    {crisis_guidelines}
    
    ตอบเพียงคำเดียว: "CRISIS" หรือ "SAFE"
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,  # ตั้งเป็น 0 เพื่อความแม่นยำและแน่นอน
        ),
    )
    return "CRISIS" in response.text.strip().upper()


# 4. ฟังก์ชันสร้างคำตอบทั่วไป
def generate_response(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
        ),
    )
    return response.text
# ส่วนการทำงานในช่องแชต Streamlit
if prompt := st.chat_input("พิมพ์ข้อความเพื่อพูดคุย..."):
    # แสดงข้อความผู้ใช้
    st.chat_message("user").write(prompt)

    with st.spinner("กำลังรับฟัง..."):
        is_crisis = check_crisis_with_ai(prompt)

    with st.chat_message("assistant"):
        if is_crisis:
            ans = """เรารู้สึกเป็นห่วงคุณมากๆ และรับรู้ว่าสิ่งที่คุณแบกรับอยู่อาจหนักหนาสาหัสเกินไปในตอนนี้ 💙
เราอยากให้คุณได้คุยกับผู้เชี่ยวชาญที่พร้อมรับฟังและช่วยเหลือคุณอย่างแท้จริง:

* **สายด่วนสุขภาพจิต:** 1323 (โทรฟรีตลอด 24 ชั่วโมง)
* **ศูนย์ช่วยเหลือของสถาบัน/มหาวิทยาลัย**
* **สายด่วนสะมาริตันส์:** 02-109-7950"""
            st.warning(ans)
        else:
            ans = generate_response(prompt)
            st.write(ans)
