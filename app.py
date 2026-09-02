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

# 2. เมนูด้านข้าง (Sidebar)
with st.sidebar:
    st.header("🚨 ช่วยเหลือฉุกเฉิน")
    st.error("**สายด่วนสุขภาพจิต:** 1323 (ฟรี 24 ชม.)")
    st.info("**สมาคมสะมาริตันส์:** 02-113-6789")
    st.caption("สามารถติดต่อศูนย์สุขภาวะจิตหรือห้องแนะแนวของมหาวิทยาลัยได้เช่นกัน")
    st.divider()
    if st.button("🔄 ล้างประวัติการคุย", use_container_width=True):
        st.session_state.messages = []
        if "chat" in st.session_state:
            del st.session_state["chat"]
        st.rerun()

st.title("🌱 SafeSpace: เพื่อนรับฟังนักศึกษา")
st.caption("พื้นที่ปลอดภัยสำหรับระบายและแยกแยะปัญหา ไม่มีการเก็บข้อมูลส่วนบุคคล (ไม่ใช่บริการทางการแพทย์)")

# 3. ฟังก์ชันโหลดคลังคำวิกฤตและคลังความรู้ทั่วไป
def load_crisis_keywords(file_path="crisis_words.txt"):
    keywords = []
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    cleaned = line.strip().lower()
                    if cleaned and not cleaned.startswith("#"):
                        keywords.append(cleaned)
        else:
            keywords = ["อยากตาย", "ไม่อยากอยู่แล้ว", "ฆ่าตัวตาย", "ทำร้ายตัวเอง", "กรีดแขน", "ลาโลก"]
    except Exception:
        keywords = ["อยากตาย", "ไม่อยากอยู่แล้ว", "ฆ่าตัวตาย", "ทำร้ายตัวเอง", "กรีดแขน", "ลาโลก"]
    return keywords

def load_general_knowledge(file_path="general_knowledge.txt"):
    """อ่านคลังแนวทางการคุย / ข้อมูลความรู้เฉพาะทางของมหาวิทยาลัย"""
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        pass
    return ""

CRISIS_FALLBACK_LIST = load_crisis_keywords()
KNOWLEDGE_BASE = load_general_knowledge()

# 4. กำหนด System Instruction โดยนำคลังความรู้ทั่วไปมาประกอบ
BASE_INSTRUCTION = """
คุณคือ "รุ่นพี่รับฟัง" ที่ปรึกษาชีวิตสำหรับนักศึกษา ป.ตรี
- บุคลิก: อบอุ่น สุภาพ เป็นกันเอง รับฟังอย่างเข้าใจ ไม่ตัดสิน
- หน้าที่: พูดคุยทักทายได้ปกติ และช่วยรับฟัง/แยกแยะปัญหาเมื่อน้องๆ เล่าเรื่องเครียดให้ฟัง
- เทคนิคการตอบ: เน้นสะท้อนความรู้สึก (Empathy) รับฟังก่อนให้คำแนะนำเชิงตรรกะ และไม่กดดันผู้ใช้
"""

FULL_SYSTEM_INSTRUCTION = f"""{BASE_INSTRUCTION}

[คลังแนวทางการตอบและข้อมูลอ้างอิงเพิ่มเติม]:
{KNOWLEDGE_BASE if KNOWLEDGE_BASE else "ตอบตามบริบททั่วไปอย่างเห็นอกเห็นใจ"}
"""

# 5. ตรวจสอบ API Key ผ่าน Secrets
raw_key = "AIzaSyChjg9f2e4k8jWv7V-QV3e5gmdrN58u74k"
if not raw_key:
    st.warning("🌱 ระบบกำลังอยู่ระหว่างการบำรุงรักษาการเชื่อมต่อ กรุณาลองใหม่อีกครั้งในภายหลังครับ")
    st.stop()

api_key = str(raw_key).strip().replace('"', '').replace("'", "")

# 6. สร้าง Client และ Chat Session พร้อมดักจับข้อผิดพลาด
try:
    if "client" not in st.session_state:
        st.session_state.client = genai.Client(api_key=api_key)

    if "chat" not in st.session_state:
        st.session_state.chat = st.session_state.client.chats.create(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                system_instruction=FULL_SYSTEM_INSTRUCTION,
                temperature=0.7,
            )
        )
except Exception:
    st.warning("🌱 ขออภัยด้วยนะครับ ระบบสัญญาณขัดข้องชั่วคราว กำลังเชื่อมต่อใหม่อีกครั้ง...")
    st.stop()

# 7. ฟังก์ชัน AI Guardrail ตรวจสอบความเสี่ยง
def check_crisis_with_ai(user_text: str) -> bool:
    safety_prompt = f"""
    วิเคราะห์ข้อความต่อไปนี้ของผู้ใช้ ว่ามีสัญญาณของการทำร้ายตัวเอง (Self-harm), การฆ่าตัวตาย (Suicide), 
    หรือความสิ้นหวังในชีวิตขั้นรุนแรงหรือไม่ (ไม่ว่าจะพูดตรงๆ หรือบอกใบ้/ใช้คำอุปมา):
    
    ข้อความ: "{user_text}"
    
    ให้ตอบเพียงคำเดียวเท่านั้น:
    - ตอบ "CRISIS" หากมีแนวโน้มหรือสัญญาณอันตราย
    - ตอบ "SAFE" หากเป็นการพูดคุยทั่วไป ปัญหาการเรียน หรือความเครียดปกติที่ไม่มีความเสี่ยงต่อชีวิต
    """
    try:
        res = st.session_state.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=safety_prompt,
        )
        return "CRISIS" in (res.text or "").strip().upper()
    except Exception:
        return any(w in user_text.lower() for w in CRISIS_FALLBACK_LIST)

# 8. จัดการประวัติข้อความ
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 9. ปุ่มเริ่มด่วน
quick_text = None
if not st.session_state.messages:
    st.write("💡 **หรือเลือกประเด็นเริ่มต้น:**")
    col1, col2, col3 = st.columns(3)
    if col1.button("📚 เครียดเรื่องเรียน", use_container_width=True):
        quick_text = "ช่วงนี้เครียดเรื่องเรียนกับการทำโปรเจกต์มาก จัดการเวลาไม่ทันเลย"
    if col2.button("👥 ปัญหาเพื่อน", use_container_width=True):
        quick_text = "มีปัญหากับเพื่อนในกลุ่มทำงาน ไม่รู้จะเริ่มพูดยังไงดี"
    if col3.button("🔋 รู้สึกหมดไฟ", use_container_width=True):
        quick_text = "รู้สึกหมดพลัง ไม่อยากทำอะไรเลย เคว้งกับอนาคตมาก"

# 10. รับและประมวลผลข้อความ
prompt = st.chat_input("พิมพ์ทักทาย หรือเล่าเรื่องในใจได้เลย...") or quick_text

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("กำลังรับฟัง..."):
        is_crisis = check_crisis_with_ai(prompt)

    with st.chat_message("assistant"):
        if is_crisis:
            ans = """
เรารู้สึกเป็นห่วงคุณมากๆ และรับรู้ว่าสิ่งที่คุณแบกรับอยู่อาจหนักหนาสาหัสเกินไปในตอนนี้ 💙  
เราอยากให้คุณได้คุยกับผู้เชี่ยวชาญที่พร้อมรับฟังและช่วยเหลือคุณอย่างแท้จริง:

- **สายด่วนสุขภาพจิต:** 1323 (โทรฟรี 24 ชม.)
- **สมาคมสะมาริตันส์แห่งประเทศไทย:** 02-113-6789
- **ศูนย์สุขภาวะจิต / ห้องแนะแนวของมหาวิทยาลัย**

คุณไม่ได้อยู่ตัวคนเดียวนะ ลองคุยกับสายด่วนหรือคนใกล้ตัวที่ไว้ใจก่อนได้ไหม?
"""
            st.error("⚠️ ระบบตรวจพบสัญญาณความเสี่ยงต่อความปลอดภัย")
            st.markdown(ans)
        else:
            try:
                response = st.session_state.chat.send_message(prompt)
                ans = response.text
                st.markdown(ans)
            except Exception:
                ans = "ขออภัยด้วยนะครับ พอดีระบบสัญญาณสะดุดไปชั่วขณะ รบกวนพิมพ์ส่งใหม่อีกครั้ง หรือกดปุ่มรีเฟรชที่เมนูด้านซ้ายนะ 🌱"
                st.info(ans)

    st.session_state.messages.append({"role": "assistant", "content": ans})
