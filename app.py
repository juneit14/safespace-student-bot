import os
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="SafeSpace - เพื่อนรับฟังนักศึกษา", page_icon="🌱", layout="centered")

# Sidebar: ช่องทางช่วยเหลือฉุกเฉิน
with st.sidebar:
    st.header("🚨 พื้นที่ช่วยเหลือฉุกเฉิน")
    st.write("หากรู้สึกไม่ไหว สามารถโทรหาผู้เชี่ยวชาญได้ทันที:")
    st.info("**สายด่วนสุขภาพจิต:** 1323 (โทรฟรี 24 ชม.)\n\n**สะมาริตันส์:** 02-113-6789")
    if st.button("ล้างประวัติการคุย"):
        st.session_state.messages = []
        if "chat" in st.session_state:
            del st.session_state["chat"]
        st.rerun()

st.title("🌱 SafeSpace: เพื่อนรับฟังนักศึกษา")
st.caption("พื้นที่ปลอดภัยสำหรับระบายและแยกแยะปัญหา (ไม่มีการบันทึกข้อมูลส่วนบุคคล)")

SYSTEM_INSTRUCTION = """
คุณคือ "รุ่นพี่รับฟัง" ที่ปรึกษาชีวิตสำหรับนักศึกษา ป.ตรี
- บุคลิก: อบอุ่น รับฟังอย่างเข้าอกเข้าใจ (Active Listening) ไม่ตัดสิน และไม่สั่งสอน
- วิธีการพูดคุย: ชวนแยกแยะปัญหาออกเป็นส่วนๆ (สิ่งที่ควบคุมได้ vs ควบคุมไม่ได้) และตั้งคำถามเปิดเพื่อช่วยให้ผู้ใช้คิดหาทางออกของตัวเอง
- ขอบเขต: ย้ำเสมอว่าตนเองเป็น AI รับฟัง ไม่ใช่ผู้เชี่ยวชาญทางการแพทย์
"""

CRISIS_KEYWORDS = ["อยากตาย", "ไม่อยากอยู่แล้ว", "ฆ่าตัวตาย", "ทำร้ายตัวเอง", "กรีดแขน", "จบชีวิต", "ลาโลก"]

# จัดการ Client และ Chat Session
api_key = st.secrets.get("AQ.Ab8RN6JBje456450PodASKDoul9DcNgoktE9PfKwcuIPCdb_IQ", os.getenv("AQ.Ab8RN6JBje456450PodASKDoul9DcNgoktE9PfKwcuIPCdb_IQ"))

if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=api_key)

if "chat" not in st.session_state:
    st.session_state.chat = st.session_state.client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.7,
        )
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

# แสดงประวัติการสนทนา
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Quick Prompts สำหรับผู้ใช้ที่ยังไม่รู้จะเริ่มอย่างไร
if not st.session_state.messages:
    st.write("หรือเลือกหัวข้อที่คุณกำลังกังวล:")
    cols = st.columns(3)
    quick_text = None
    if cols[0].button("📚 เครียดเรื่องโปรเจกต์/สอบ"):
        quick_text = "ช่วงนี้เครียดเรื่องเรียนกับการทำโปรเจกต์มาก จัดการเวลาไม่ทันเลย"
    if cols[1].button("👥 ปัญหาเพื่อนร่วมกลุ่ม"):
        quick_text = "มีปัญหากับเพื่อนในกลุ่มทำงาน ไม่รู้จะคุยยังไงดี"
    if cols[2].button("🔋 รู้สึกหมดไฟ เคว้งคว้าง"):
        quick_text = "รู้สึกหมดพลัง ไม่อยากทำอะไรเลย เคว้งกับอนาคตมาก"
else:
    quick_text = None

# รับ Input
prompt = st.chat_input("พิมพ์เล่าเรื่องที่อยู่ในใจตรงนี้ได้เลย...") or quick_text

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # ตรวจสอบวิกฤต
    is_crisis = any(kw in prompt.lower() for kw in CRISIS_KEYWORDS)

    with st.chat_message("assistant"):
        if is_crisis:
            response_text = (
                "เรารับรู้ได้ว่าสิ่งที่คุณแบกรับอยู่อาจหนักหนาสาหัสเกินไปในตอนนี้ 💙\n\n"
                "เราอยากให้คุณได้คุยกับผู้เชี่ยวชาญที่พร้อมรับฟังและช่วยเหลือคุณอย่างแท้จริง:\n"
                "- **สายด่วนสุขภาพจิต:** 1323 (โทรฟรีตลอด 24 ชม.)\n"
                "- **สมาคมสะมาริตันส์:** 02-113-6789\n\n"
                "คุณไม่ได้อยู่ตัวคนเดียวนะ ลองติดต่อสายด่วนหรือคนใกล้ตัวที่ไว้ใจก่อนได้ไหม?"
            )
            st.error("⚠️ แจ้งเตือนความปลอดภัย")
            st.markdown(response_text)
        else:
            response = st.session_state.chat.send_message(prompt)
            response_text = response.text
            st.markdown(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
