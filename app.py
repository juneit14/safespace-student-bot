import os
import streamlit as st
from google import genai
from google.genai import types

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="OmniAgent - ผู้ช่วยอัจฉริยะ", 
    page_icon="⚡", 
    layout="centered"
)

# 2. เมนูด้านข้าง (Sidebar)
with st.sidebar:
    st.header("⚙️ ตัวช่วย & เมนู")
    if st.button("🔄 ล้างการสนทนา", use_container_width=True):
        st.session_state.messages = []
        if "chat" in st.session_state:
            del st.session_state["chat"]
        st.rerun()
    st.caption("AI เปิดใช้ความสามารถค้นหาข้อมูลเรียลไทม์ (Google Search)")

st.title("⚡ Smart AI Agent")
st.caption("ถามได้ทุกเรื่อง: ความรู้รอบตัว, เขียนโค้ด, วิเคราะห์ข้อมูล, ปรึกษาปัญหาชีวิต")

# 3. System Instruction แบบอเนกประสงค์ ปรับตัวตามคำถาม
SYSTEM_INSTRUCTION = """
คุณคือ AI Agent ผู้ช่วยอัจฉริยะรอบรู้ ปรับสไตล์การตอบตามเจตนาของผู้ใช้:
1. คำถามเชิงข้อเท็จจริง/วิชาการ/โค้ดดิ้ง: ตอบตรงประเด็น แม่นยำ กระชับ จัดระเบียบด้วยข้อความชัดเจน
2. ขอคำปรึกษา/ระบายความรู้สึก: รับฟังอย่างเข้าอกเข้าใจ ใช้ภาษาอบอุ่น เป็นกันเอง ไม่ตัดสิน
3. คำถามซับซ้อน: คิดวิเคราะห์เป็นขั้นตอน ไม่เดา หากข้อมูลไม่แน่ใจให้ค้นหาคำตอบ
4. ข้อควรระวังความปลอดภัย: หากพบเจตนาทำร้ายตนเองอย่างชัดเจน ให้แสดงความห่วงใยพร้อมแนะนำสายด่วน 1323 ทันที
"""

# 4. ตรวจสอบ API Key
raw_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
if not raw_key:
    st.warning("⚠️ ไม่พบ GEMINI_API_KEY กรุณาตั้งค่าใน Streamlit Secrets หรือ Environment Variable")
    st.stop()

api_key = str(raw_key).strip().replace('"', '').replace("'", "")

# 5. สร้าง Client และ Chat Session พร้อมเปิด Google Search
try:
    if "client" not in st.session_state:
        st.session_state.client = genai.Client(api_key=api_key)

    if "chat" not in st.session_state:
        st.session_state.chat = st.session_state.client.chats.create(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
                tools=[{"google_search": {}}]  # เชื่อม Web Search ให้หาข้อมูลอัปเดตได้
            )
        )
except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}")
    st.stop()

# 6. จัดการประวัติข้อความ
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 7. รับและประมวลผลข้อความ
prompt = st.chat_input("ถามคำถาม, ให้ช่วยเขียนโค้ด, วางแผนงาน หรือชวนคุยได้เลย...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("กำลังคิดคำตอบ..."):
            try:
                response = st.session_state.chat.send_message(prompt)
                ans = response.text
                st.markdown(ans)
            except Exception as e:
                ans = f"ขออภัยด้วยครับ เกิดข้อผิดพลาดชั่วคราว: {e}"
                st.warning(ans)

    st.session_state.messages.append({"role": "assistant", "content": ans})
