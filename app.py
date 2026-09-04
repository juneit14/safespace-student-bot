import os
import time
import streamlit as st
from google import genai
from google.genai import types

# 1. ตั้งค่าหน้าเว็บและแถบข้าง
st.set_page_config(page_title="SafeSpace - เพื่อนรับฟังนักศึกษา", page_icon="🌱", layout="centered")

with st.sidebar:
    st.header("🚨 ช่วยเหลือฉุกเฉิน")
    st.error("**สายด่วนสุขภาพจิต:** 1323 (ฟรี 24 ชม.)")
    st.info("**สมาคมสะมาริตันส์:** 02-113-6789")
    st.caption("สามารถติดต่อศูนย์สุขภาวะจิตหรือห้องแนะแนวของมหาวิทยาลัยได้เช่นกัน")
    st.divider()
    if st.button("🔄 ล้างประวัติการคุย", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.title("🌱 SafeSpace: เพื่อนรับฟังนักศึกษา")
st.caption("พื้นที่ปลอดภัยสำหรับระบายและแยกแยะปัญหา ไม่มีการเก็บข้อมูลส่วนบุคคล (ไม่ใช่บริการทางการแพทย์)")

# 2. ฟังก์ชันโหลดข้อมูลคำสำคัญและคลังความรู้
def load_crisis_keywords(file_path="crisis_words.txt"):
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return [line.strip().lower() for line in f if line.strip() and not line.startswith("#")]
    except Exception:
        pass
    return ["อยากตาย", "ไม่อยากอยู่แล้ว", "ฆ่าตัวตาย", "ทำร้ายตัวเอง", "กรีดแขน", "ลาโลก"]

def load_general_knowledge(file_path="general_knowledge.txt"):
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        pass
    return ""

CRISIS_FALLBACK_LIST = load_crisis_keywords()
KNOWLEDGE_BASE = load_general_knowledge()

# 3. กำหนด System Instruction
SYSTEM_INSTRUCTION = f"""
คุณคือ "รุ่นพี่รับฟัง" รุ่นพี่มหาวิทยาลัยที่เปิดใจรับฟังรุ่นน้อง ป.ตรี
- บุคลิก: อบอุ่น เป็นกันเอง สุภาพแต่เข้าถึงง่าย ภาษาพูดเป็นธรรมชาติ มีคำลงท้ายนุ่มนวล เช่น "ครับ/นะ/เนอะ" ไม่พิมพ์ยาวเป็นเรียงความ
- การตอบตามสถานการณ์:
  1. การทักทาย / คุยทั่วไป: ตอบรับสดใส สั้นกระชับ เป็นมิตร ห้ามด่วนสรุปว่าน้องกำลังมีปัญหาจนกว่าน้องจะเล่า
  2. การระบายปัญหา: ใช้ทักษะ Active Listening สะท้อนอารมณ์ ไม่รีบยัดเยียดทางแก้ ชวนคุยต่อด้วยคำถามปลายเปิดสั้นๆ

[คลังข้อมูลอ้างอิงเพิ่มเติม]:
{KNOWLEDGE_BASE if KNOWLEDGE_BASE else "ตอบตามบริบททั่วไปอย่างเห็นอกเห็นใจ"}
"""

# 4. ตรวจสอบ API Key และสร้าง Client
raw_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
if not raw_key:
    st.warning("🌱 ระบบกำลังอยู่ระหว่างการบำรุงรักษาการเชื่อมต่อ กรุณาลองใหม่อีกครั้งในภายหลังครับ")
    st.stop()

if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=str(raw_key).strip().replace('"', '').replace("'", ""))

# 5. ฟังก์ชันตรวจสอบความเสี่ยง
def check_crisis_with_ai(user_text: str) -> bool:
    clean_text = user_text.strip().lower()
    if clean_text in ["หวัดดี", "สวัสดี", "ดีครับ", "ดีค่ะ", "hi", "hello", "ว่าไง", "ฮัลโหล"]:
        return False

    prompt = f'วิเคราะห์ข้อความว่ามีสัญญาณฆ่าตัวตาย ทำร้ายตัวเอง หรือสิ้นหวังขั้นรุนแรงหรือไม่: "{user_text}"\nตอบเฉพาะ "CRISIS" หรือ "SAFE"'
    try:
        res = st.session_state.client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        return "CRISIS" in (res.text or "").strip().upper()
    except Exception:
        return any(w in clean_text for w in CRISIS_FALLBACK_LIST)

# 6. แสดงประวัติการสนทนา
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 7. ปุ่มเริ่มด่วน
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

# 8. รับและประมวลผลข้อความ
prompt = st.chat_input("พิมพ์ทักทาย หรือเล่าเรื่องในใจได้เลย...") or quick_text

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("กำลังรับฟัง..."):
            is_crisis = check_crisis_with_ai(prompt)

        if is_crisis:
            ans = (
                "เรารู้สึกเป็นห่วงคุณมากๆ และรับรู้ว่าสิ่งที่คุณแบกรับอยู่อาจหนักหนาสาหัสเกินไปในตอนนี้ 💙\n\n"
                "เราอยากให้คุณได้คุยกับผู้เชี่ยวชาญที่พร้อมรับฟังและช่วยเหลือคุณอย่างแท้จริง:\n"
                "- **สายด่วนสุขภาพจิต:** 1323 (โทรฟรี 24 ชม.)\n"
                "- **สมาคมสะมาริตันส์แห่งประเทศไทย:** 02-113-6789\n"
                "- **ศูนย์สุขภาวะจิต / ห้องแนะแนวของมหาวิทยาลัย**\n\n"
                "คุณไม่ได้อยู่ตัวคนเดียวนะ ลองคุยกับสายด่วนหรือคนใกล้ตัวที่ไว้ใจก่อนได้ไหม?"
            )
            st.error("⚠️ ระบบตรวจพบสัญญาณความเสี่ยงต่อความปลอดภัย")
            st.markdown(ans)
        else:
            try:
                recent_msgs = st.session_state.messages[-4:]
                history = [
                    types.Content(
                        role="user" if m["role"] == "user" else "model",
                        parts=[types.Part.from_text(text=m["content"])]
                    ) for m in recent_msgs
                ]
                
                # ลองส่งคำขอ หากติด Rate Limit ให้รอ 4 วินาทีแล้วลองใหม่ 1 ครั้ง
                response = None
                for attempt in range(2):
                    try:
                        response = st.session_state.client.models.generate_content(
                            model="gemini-3.6-flash",  # ใช้รุ่นที่ระบบรองรับ
                            contents=history,
                            config=types.GenerateContentConfig(
                                system_instruction=SYSTEM_INSTRUCTION,
                                temperature=0.7,
                                max_output_tokens=800,
                            )
                        )
                        break
                    except Exception as err:
                        if "429" in str(err) and attempt == 0:
                            time.sleep(4)  # หน่วงเวลารอคิว Free Tier ตามที่ Google ร้องขอ
                            continue
                        raise err

                ans = response.text
                st.markdown(ans)
            except Exception as e:
                ans = f"เกิดข้อผิดพลาดจากระบบ: {e}"
                st.error(ans)

    st.session_state.messages.append({"role": "assistant", "content": ans})
