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
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        pass
    return ""

CRISIS_FALLBACK_LIST = load_crisis_keywords()
KNOWLEDGE_BASE = load_general_knowledge()

# 4. ปรับ System Instruction ให้รองรับการทักทายและการคุยทั่วไปอย่างเป็นธรรมชาติ
BASE_INSTRUCTION = """
คุณคือ "รุ่นพี่รับฟัง" รุ่นพี่มหาวิทยาลัยที่เปิดใจรับฟังรุ่นน้อง ป.ตรี
- บุคลิก: อบอุ่น เป็นกันเอง สุภาพแต่เข้าถึงง่าย (เหมือนพี่คุยกับน้องในแช็ต ไม่ใช่ครูกับนักเรียน)
- ภาษาที่ใช้: ภาษาพูดธรรมชาติ มีคำลงท้ายนุ่มนวล เช่น "ครับ/นะ/เนอะ" ไม่พิมพ์ยาวเป็นเรียงความ

- รูปแบบการตอบตามสถานการณ์:
  1. การทักทาย / คุยเล่นทั่วไป (Small Talk): 
     * ตอบรับอย่างสดใส เป็นมิตร สั้นกระชับ (เช่น "สวัสดีครับน้อง มีเรื่องอะไรอยากคุยหรืออยากระบายให้พี่ฟังไหม สบายๆ ได้เลยนะ")
     * ห้ามด่วนสรุปว่าน้องกำลังเครียดหรือมีปัญหาจนกว่าน้องจะเล่าออกมาเอง
  2. เมื่อน้องเริ่มระบายปัญหาหรือความเครียด:
     * ใช้ทักษะ Active Listening: สะท้อนความรู้สึก รับฟัง ไม่ด่วนตัดสิน และไม่รีบยัดเยียดทางแก้
     * ชวนคุยต่อด้วยคำถามปลายเปิดสั้นๆ ทีละนิด
"""

FULL_SYSTEM_INSTRUCTION = f"""{BASE_INSTRUCTION}

[คลังแนวทางการตอบและข้อมูลอ้างอิงเพิ่มเติม]:
{KNOWLEDGE_BASE if KNOWLEDGE_BASE else "ตอบตามบริบททั่วไปอย่างเห็นอกเห็นใจ"}
"""

# 5. ตรวจสอบ API Key ผ่าน Secrets
raw_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
if not raw_key:
    st.warning("🌱 ระบบกำลังอยู่ระหว่างการบำรุงรักษาการเชื่อมต่อ กรุณาลองใหม่อีกครั้งในภายหลังครับ")
    st.stop()

api_key = str(raw_key).strip().replace('"', '').replace("'", "")

# 6. สร้าง Client และ Chat Session
try:
    if "client" not in st.session_state:
        st.session_state.client = genai.Client(api_key=api_key)

    if "chat" not in st.session_state:
        st.session_state.chat = st.session_state.client.chats.create(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                system_instruction=FULL_SYSTEM_INSTRUCTION,
                temperature=0.7,
                top_p=0.95
            )
        )
except Exception:
    st.warning("🌱 ขออภัยด้วยนะครับ ระบบสัญญาณขัดข้องชั่วคราว กำลังเชื่อมต่อใหม่อีกครั้ง...")
    st.stop()

# 7. ฟังก์ชัน AI Guardrail ตรวจสอบความเสี่ยง (ข้ามคำทักทายสั้นๆ เพื่อประหยัดเวลา)
def check_crisis_with_ai(user_text: str) -> bool:
    clean_text = user_text.strip().lower()
    common_greetings = ["หวัดดี", "สวัสดี", "ดีครับ", "ดีค่ะ", "hi", "hello", "ว่าไง", "ฮัลโหล"]
    if clean_text in common_greetings:
        return False

    safety_prompt = f"""
    วิเคราะห์ข้อความต่อไปนี้ของผู้ใช้ ว่ามีสัญญาณของการทำร้ายตัวเอง (Self-harm), การฆ่าตัวตาย (Suicide), 
    หรือความสิ้นหวังในชีวิตขั้นรุนแรงหรือไม่:
    
    ข้อความ: "{user_text}"
    
    ให้ตอบเพียงคำเดียวเท่านั้น:
    - ตอบ "CRISIS" หากมีแนวโน้มหรือสัญญาณอันตราย
    - ตอบ "SAFE" หากเป็นการพูดคุยทั่วไป ทักทาย ปัญหาการเรียน หรือความเครียดปกติที่ไม่มีความเสี่ยงต่อชีวิต
    """
    try:
        res = st.session_state.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=safety_prompt,
        )
        return "CRISIS" in (res.text or "").strip().upper()
    except Exception:
        return any(w in clean_text for w in CRISIS_FALLBACK_LIST)

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

    with st.spinner("กำลังพิมพ์..."):
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
               # รวบรวมบริบทและส่งคำตอบ
                chat_history = []
                for m in st.session_state.messages:
                    role = "user" if m["role"] == "user" else "model"
                    chat_history.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))

                response = st.session_state.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=chat_history,
                config=types.GenerateContentConfig(
                    system_instruction=FULL_SYSTEM_INSTRUCTION,
                    temperature=0.7,
                )
            )
        ans = response.text
        st.markdown(ans)
        except Exception as e:
           ans = f"เกิดข้อผิดพลาดจากระบบ: {e}"
           st.error(ans)

    st.session_state.messages.append({"role": "assistant", "content": ans})
