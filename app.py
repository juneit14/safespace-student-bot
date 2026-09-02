%%writefile app.py
import streamlit as st
from google import genai
from google.genai import types

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="SafeSpace - เพื่อนรับฟังนักศึกษา", page_icon="🌱")
st.title("🌱 SafeSpace: พื้นที่รับฟังสำหรับนักศึกษา")
st.caption("AI รับฟังและช่วยแยกแยะปัญหา ไม่มีการเก็บข้อมูลระบุตัวตน (ไม่ใช่บริการทางการแพทย์)")

CRISIS_KEYWORDS = [
    "อยากตาย", "ไม่อยากอยู่แล้ว", "ฆ่าตัวตาย", "ทำร้ายตัวเอง", 
    "กรีดแขน", "จบชีวิต", "ทรมานเหลือเกิน", "ลาโลก"
]

CRISIS_RESPONSE = """
เรารู้สึกเป็นห่วงคุณมากๆ และรับรู้ว่าสิ่งที่คุณแบกรับอยู่อาจหนักหนาสาหัสเกินไปในตอนนี้ 💙  
แม้เราเป็น AI ที่พร้อมรับฟัง แต่เราอยากให้คุณได้รับความช่วยเหลือจากผู้เชี่ยวชาญโดยตรง:

- **สายด่วนสุขภาพจิต:** 1323 (ฟรีตลอด 24 ชม.)
- **สมาคมสะมาริตันส์แห่งประเทศไทย:** 02-113-6789 (12:00 - 22:00 น.)
- **ศูนย์สุขภาวะจิต / ห้องแนะแนวของมหาวิทยาลัยของคุณ**

คุณไม่ได้อยู่คนเดียวนะ ลองคุยกับสายด่วนหรือคนใกล้ตัวที่ไว้ใจก่อนได้ไหม?
"""

SYSTEM_INSTRUCTION = """
คุณคือ "รุ่นพี่รับฟัง" ที่ปรึกษาชีวิตสำหรับนักศึกษา ป.ตรี
- บุคลิก: อบอุ่น สุภาพ ไม่ตัดสิน รับฟังอย่างเข้าอกเข้าใจ (Active Listening)
- วิธีการตอบ: สะท้อนความรู้สึกของผู้ใช้ ชวนคิดและแยกแยะปัญหาเป็นข้อๆ ไม่สั่งสอน ไม่ยัดเยียดทางแก้สำเร็จรูป
- ขอบเขต: ย้ำเสมอว่าตนเองไม่ใช่จิตแพทย์ หากพบปัญหาสุขภาพจิตลึกซึ้ง ให้แนะนำช่องทางปรึกษาของมหาวิทยาลัย
"""

if "client" not in st.session_state:
    # วาง API Key ที่ขอมาตรงนี้
    st.session_state.client = genai.Client(api_key="AQ.Ab8RN6JBje456450PodASKDoul9DcNgoktE9PfKwcuIPCdb_IQ")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("พิมพ์ระบายหรือเล่าเรื่องที่กังวลใจได้ที่นี่..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    is_crisis = any(kw in prompt.lower() for kw in CRISIS_KEYWORDS)

    with st.chat_message("assistant"):
        if is_crisis:
            response_text = CRISIS_RESPONSE
            st.error("⚠️ แจ้งเตือนความปลอดภัย")
            st.markdown(response_text)
        else:
            response = st.session_state.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.7,
                )
            )
            response_text = response.text
            st.markdown(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
