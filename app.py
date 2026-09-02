import os
import streamlit as st
from google import genai
from google.genai import types

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="SafeSpace - เพื่อนรับฟังนักศึกษา", 
    page_icon="🌱", 
    layout="centered"
)

# 2. เมนูด้านข้าง (Sidebar) สำหรับช่องทางช่วยเหลือฉุกเฉิน
with st.sidebar:
    st.header("🚨 ช่วยเหลือฉุกเฉิน")
    st.write("หากรู้สึกไม่ไหวหรือต้องการคุยกับผู้เชี่ยวชาญทันที:")
    st.error("**สายด่วนสุขภาพจิต:** 1323 (โทรฟรี 24 ชม.)")
    st.info("**สมาคมสะมาริตันส์:** 02-113-6789 (12:00 - 22:00 น.)")
    st.caption("สามารถติดต่อศูนย์สุขภาวะจิตหรือห้องแนะแนวของมหาวิทยาลัยได้เช่นกัน")
    
    st.divider()
    if st.button("🔄 ล้างบทสนทนา / เริ่มคุยใหม่", use_container_width=True):
        st.session_state.messages = []
        if "chat" in st.session_state:
            del st.session_state["chat"]
        st.rerun()

# 3. หัวข้อหน้าเว็บ
st.title("🌱 SafeSpace: เพื่อนรับฟังนักศึกษา")
st.caption("พื้นที่ปลอดภัยสำหรับระบายและแยกแยะปัญหา ไม่มีการเก็บข้อมูลส่วนบุคคล (ไม่ใช่บริการทางการแพทย์)")

# 4. กำหนดบทบาทและคำค้นหาความเสี่ยง
SYSTEM_INSTRUCTION = """
คุณคือ "รุ่นพี่รับฟัง" ที่ปรึกษาชีวิตสำหรับนักศึกษา ป.ตรี
- บุคลิก: อบอุ่น สุภาพ รับฟังอย่างเข้าอกเข้าใจ (Active Listening) ไม่ตัดสิน และไม่สั่งสอน
- วิธีการพูดคุย: สะท้อนความรู้สึก ชวนแยกแยะปัญหาออกเป็นส่วนๆ (สิ่งที่ควบคุมได้ vs สิ่งที่ต้องปล่อยวาง) และตั้งคำถามเปิดเพื่อช่วยให้ผู้ใช้คิดหาทางออกของตนเอง
- ขอบเขต: ย้ำเสมอว่าตนเองเป็น AI รับฟัง ไม่ใช่แพทย์ หากพบปัญหาสุขภาพจิตลึกซึ้ง ให้แนะนำช่องทางปรึกษาของมหาวิทยาลัยหรือสายด่วนสุขภาพจิต
"""

CRISIS_KEYWORDS = [
    "อยากตาย", "ไม่อยากอยู่แล้ว", "ฆ่าตัวตาย", "ทำร้ายตัวเอง", 
    "กรีดแขน", "จบชีวิต", "ทรมานเหลือเกิน", "ลาโลก"
]

CRISIS_RESPONSE = """
เรารู้สึกเป็นห่วงคุณมากๆ และรับรู้ว่าสิ่งที่คุณแบกรับอยู่อาจหนักหนาสาหัสเกินไปในตอนนี้ 💙  
เราอยากให้คุณได้รับความช่วยเหลือจากผู้เชี่ยวชาญที่พร้อมรับฟังโดยตรง:

- **สายด่วนสุขภาพจิต:** 1323 (ฟรีตลอด 24 ชม.)
- **สมาคมสะมาริตันส์แห่งประเทศไทย:** 02-113-6789
- **ศูนย์สุขภาวะจิต / ห้องแนะแนวของมหาวิทยาลัย**

คุณไม่ได้อยู่ตัวคนเดียวนะ ลองคุยกับสายด่วนหรือคนใกล้ตัวที่ไว้ใจก่อนได้ไหม?
"""

# 5. จัดการ Client และ Multi-turn Chat Session
api_key = st.secrets.get("AQ.Ab8RN6JBje456450PodASKDoul9DcNgoktE9PfKwcuIPCdb_IQ", os.getenv("AQ.Ab8RN6JBje456450PodASKDoul9DcNgoktE9PfKwcuIPCdb_IQ"))

if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=api_key)

# ใช้โมเดล gemini-2.5-flash พร้อมเก็บประวัติบทสนทนา (Multi-turn)
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

# แสดงประวัติการแช็ตทั้งหมด
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ปุ่มลัดเลือกประเด็น สำหรับคนที่ยังไม่รู้จะเริ่มคุยอย่างไร
quick_text = None
if not st.session_state.messages:
    st.write("💡 **หรือเลือกประเด็นที่คุณกำลังกังวลอยู่:**")
    col1, col2, col3 = st.columns(3)
    if col1.button("📚 เครียดเรื่องเรียน/โปรเจกต์", use_container_width=True):
        quick_text = "ช่วงนี้เครียดเรื่องเรียนกับการทำโปรเจกต์มาก จัดการเวลาไม่ทันเลย"
    if col2.button("👥 ปัญหาเพื่อนร่วมกลุ่ม", use_container_width=True):
        quick_text = "มีปัญหากับเพื่อนในกลุ่มทำงาน ไม่รู้จะเริ่มพูดยังไงดี"
    if col3.button("🔋 รู้สึกหมดไฟ เคว้งคว้าง", use_container_width=True):
        quick_text = "รู้สึกหมดพลัง ไม่อยากทำอะไรเลย เคว้งกับอนาคตมาก"

# รับข้อความจากผู้ใช้ (ผ่านกล่องพิมพ์ หรือคลิกปุ่มลัด)
prompt = st.chat_input("พิมพ์ระบายหรือเล่าเรื่องที่อยู่ในใจได้ที่นี่...") or quick_text

if prompt:
    # บันทึกและแสดงข้อความของผู้ใช้
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # ตรวจสอบวิกฤตความปลอดภัย (Crisis Guardrail)
    is_crisis = any(kw in prompt.lower() for kw in CRISIS_KEYWORDS)

    with st.chat_message("assistant"):
        if is_crisis:
            response_text = CRISIS_RESPONSE
            st.error("⚠️ แจ้งเตือนความปลอดภัย")
            st.markdown(response_text)
        else:
            # ส่งข้อความคุยแบบต่อเนื่องผ่าน Chat Session ของ Gemini Flash
            response = st.session_state.chat.send_message(prompt)
            response_text = response.text
            st.markdown(response_text)

    # บันทึกคำตอบของระบบ
    st.session_state.messages.append({"role": "assistant", "content": response_text})
