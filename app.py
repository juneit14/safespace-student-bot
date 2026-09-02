import os
import streamlit as st
import google.generativeai as genai

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="SafeSpace - เพื่อนรับฟังนักศึกษา", page_icon="🌱", layout="centered")

# 2. เมนูด้านข้าง (Sidebar)
with st.sidebar:
    st.header("🚨 ช่วยเหลือฉุกเฉิน")
    st.error("**สายด่วนสุขภาพจิต:** 1323 (ฟรี 24 ชม.)")
    st.info("**สมาคมสะมาริตันส์:** 02-113-6789")
    st.divider()
    if st.button("🔄 ล้างประวัติการคุย", use_container_width=True):
        st.session_state.messages = []
        if "chat" in st.session_state:
            del st.session_state["chat"]
        st.rerun()

st.title("🌱 SafeSpace: เพื่อนรับฟังนักศึกษา")
st.caption("พื้นที่ปลอดภัยสำหรับระบายและแยกแยะปัญหา (ไม่ใช่บริการทางการแพทย์)")

# 3. System Instruction สำหรับบทบาทรุ่นพี่รับฟัง
SYSTEM_INSTRUCTION = """
คุณคือ "รุ่นพี่รับฟัง" ที่ปรึกษาชีวิตสำหรับนักศึกษา ป.ตรี
- บุคลิก: อบอุ่น สุภาพ เป็นกันเอง รับฟังอย่างเข้าใจ ไม่ตัดสิน
- หน้าที่: พูดคุยทักทายได้ปกติ และช่วยรับฟัง/แยกแยะปัญหาเมื่อน้องๆ เล่าเรื่องเครียดให้ฟัง
"""

# 4. ดึง Key และตั้งค่าระบบ
api_key = "AQ.Ab8RN6JBje456450PodASKDoul9DcNgoktE9PfKwcuIPCdb_IQ"
if not api_key:
    st.error("⚠️ ไม่พบ API Key: กรุณาตั้งค่า GEMINI_API_KEY ใน App Settings > Secrets ก่อนใช้งาน")
    st.stop()

clean_key = api_key.strip().replace('"', '').replace("'", "")
genai.configure(api_key=clean_key)

# 5. ฟังก์ชันให้ AI ตรวจสอบความเสี่ยง (วางไว้ตรงนี้เพื่อให้ส่วนล่างเรียกใช้ได้)
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
        eval_model = genai.GenerativeModel("gemini-1.5-flash")
        result = eval_model.generate_content(safety_prompt)
        return "CRISIS" in result.text.strip().upper()
    except Exception:
        fallback_words = ["อยากตาย", "ไม่อยากอยู่แล้ว", "ฆ่าตัวตาย", "ทำร้ายตัวเอง", "กรีดแขน", "ลาโลก"]
        return any(w in user_text for w in fallback_words)

# 6. จัดการ Session State สำหรับประวัติแช็ต
if "chat" not in st.session_state:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=SYSTEM_INSTRUCTION
    )
    st.session_state.chat = model.start_chat(history=[])

if "messages" not in st.session_state:
    st.session_state.messages = []

# แสดงประวัติการคุย
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ปุ่มลัดเริ่มต้น
quick_text = None
if not st.session_state.messages:
    st.write("💡 หรือเลือกหัวข้อเริ่มต้น:")
    col1, col2, col3 = st.columns(3)
    if col1.button("📚 เครียดเรื่องเรียน", use_container_width=True):
        quick_text = "ช่วงนี้เครียดเรื่องเรียนกับการทำโปรเจกต์มาก จัดการเวลาไม่ทันเลย"
    if col2.button("👥 ปัญหาเพื่อน", use_container_width=True):
        quick_text = "มีปัญหากับเพื่อนในกลุ่มทำงาน ไม่รู้จะเริ่มพูดยังไงดี"
    if col3.button("🔋 รู้สึกหมดไฟ", use_container_width=True):
        quick_text = "รู้สึกหมดพลัง ไม่อยากทำอะไรเลย เคว้งกับอนาคตมาก"

# รับ Input
prompt = st.chat_input("พิมพ์ทักทาย หรือเล่าเรื่องในใจได้เลย...") or quick_text

# --- จุดที่คุณถาม: โค้ดส่วนนี้จะอยู่ล่างสุดของไฟล์เสมอ ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 1. ให้ Gemini ประเมินความเสี่ยงทางอารมณ์ก่อน
    with st.spinner("กำลังรับฟัง..."):
        is_crisis = check_crisis_with_ai(prompt)

    with st.chat_message("assistant"):
        if is_crisis:
            # 2. หากเป็นวิกฤต แสดงข้อความช่วยเหลือทันที
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
            # 3. หากปลอดภัย ส่งต่อให้รุ่นพี่ AI ตอบตามปกติ
            try:
                response = st.session_state.chat.send_message(prompt)
                ans = response.text
                st.markdown(ans)
            except Exception as e:
                ans = f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}"
                st.error(ans)

    st.session_state.messages.append({"role": "assistant", "content": ans})
