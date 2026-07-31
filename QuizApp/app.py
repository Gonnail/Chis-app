import streamlit as st
from docx import Document
import os
import re

# --------------------
# Đường dẫn file câu hỏi
# --------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCX_FILE = os.path.join(BASE_DIR, "SOURCE SSG105.docx")


# --------------------
# Đọc file Word
# --------------------
def read_quiz(docx_path):
    doc = Document(docx_path)
    questions = []

    current_q = None
    options = []
    correct = []

    def push_question():
        nonlocal current_q, options, correct

        if current_q and options:
            questions.append({
                "question": current_q,
                "options": options.copy(),
                "correct": correct.copy(),
                "multi": len(correct) > 1
            })

    for para in doc.paragraphs:
        text = para.text.strip()

        if not text:
            continue

        # Question x
        if re.match(r"Question\s+\d+", text, re.IGNORECASE):
            push_question()

            current_q = text
            options = []
            correct = []

        # A. / B. / C. / D. / E. / F. ...
        elif re.match(r"^[A-Z]\.", text):
            option_text = re.sub(r"^[A-Z]\.\s*", "", text).strip()
            options.append(option_text)

            # Đáp án đúng được in đậm
            if any(run.bold for run in para.runs if run.text.strip()):
                correct.append(option_text)

        # Dòng tiếp theo của câu hỏi dài
        elif current_q and not options:
            current_q += " " + text

    push_question()
    return questions


# --------------------
# Kiểm tra đúng / sai
# --------------------
def is_correct(user_answer, correct_answer):
    if not correct_answer:
        return False

    if isinstance(user_answer, list):
        return set(user_answer) == set(correct_answer)

    return user_answer == correct_answer[0]


# --------------------
# Giao diện
# --------------------
st.set_page_config(
    page_title="10 Điểm SSG cùng em Chí",
    page_icon="🎮",
    layout="wide"
)

st.title("🎮 10 Điểm SSG cùng em Chí")


# --------------------
# Session riêng cho từng người
# --------------------
if "answers" not in st.session_state:
    st.session_state.answers = {}

progress = {"answers": st.session_state.answers}


# --------------------
# Đọc file câu hỏi có sẵn
# --------------------
if not os.path.exists(DOCX_FILE):
    st.error(f"❌ Không tìm thấy file: {DOCX_FILE}")
    st.stop()

quiz = read_quiz(DOCX_FILE)

st.success(f"📘 Đã đọc {len(quiz)} câu hỏi từ {os.path.basename(DOCX_FILE)}")


# --------------------
# Sidebar
# --------------------
st.sidebar.title("📚 Mục lục")

score = 0
answered = 0

for i, q in enumerate(quiz):
    ans = progress["answers"].get(str(i))

    if ans is None or ans == []:
        status = "⚪"
    else:
        answered += 1

        if is_correct(ans, q["correct"]):
            status = "🟢"
            score += 1
        else:
            status = "🔴"

    st.sidebar.markdown(f"{status} [Câu {i+1}](#q{i})")

st.sidebar.divider()
st.sidebar.metric("Đã làm", f"{answered}/{len(quiz)}")
st.sidebar.metric("Điểm hiện tại", f"{score}/{len(quiz)}")


# --------------------
# Nút làm mới bài
# --------------------
if st.sidebar.button("🔄 Bắt đầu bài mới"):
    st.session_state.answers = {}
    st.rerun()


# --------------------
# Hiển thị câu hỏi
# --------------------
for i, q in enumerate(quiz):
    st.markdown(f"<a id='q{i}'></a>", unsafe_allow_html=True)

    st.markdown(f"## Câu {i+1}")
    st.write(q["question"])

    key = str(i)

    # ===== NHIỀU ĐÁP ÁN =====
    if q["multi"]:
        required = len(q["correct"])
        st.caption(f"✅ Chọn đúng {required} đáp án")

        previous = progress["answers"].get(key) or []
        selected = []

        cols = st.columns(2)

        for idx, opt in enumerate(q["options"]):
            with cols[idx % 2]:
                checked = st.checkbox(
                    opt,
                    value=opt in previous,
                    key=f"cb_{key}_{idx}"
                )

                if checked:
                    selected.append(opt)

        # Lưu session
        if selected:
            progress["answers"][key] = selected
        else:
            progress["answers"].pop(key, None)

        st.session_state.answers = progress["answers"]

        # Chấm ngay khi chọn đủ số đáp án
        if len(selected) == required:
            if is_correct(selected, q["correct"]):
                st.success("🎉 Chính xác!")
            else:
                st.error(
                    f"❌ Sai. Đáp án đúng: **{', '.join(q['correct'])}**"
                )

    # ===== MỘT ĐÁP ÁN =====
    else:
        previous = progress["answers"].get(key)

        # Thêm lựa chọn rỗng => chưa trả lời
        radio_options = ["-- Chưa chọn --"] + q["options"]

        if previous in q["options"]:
            default_index = radio_options.index(previous)
        else:
            default_index = 0

        choice = st.radio(
            "Chọn đáp án:",
            radio_options,
            index=default_index,
            key=f"radio_{key}"
        )

        # Chỉ lưu khi đã chọn đáp án thật
        if choice == "-- Chưa chọn --":
            progress["answers"].pop(key, None)
        else:
            progress["answers"][key] = choice

        st.session_state.answers = progress["answers"]

        # Chỉ hiển thị kết quả khi đã chọn
        if choice != "-- Chưa chọn --":
            if q["correct"]:
                if choice == q["correct"][0]:
                    st.success("🎉 Chính xác!")
                else:
                    st.error(f"❌ Sai. Đáp án đúng: **{q['correct'][0]}**")
            else:
                st.warning("⚠️ Không tìm thấy đáp án đúng trong file Word.")

    st.divider()


# --------------------
# Reset thủ công
# --------------------
if st.button("🗑️ Xóa tất cả câu trả lời"):
    st.session_state.answers = {}
    st.rerun()
