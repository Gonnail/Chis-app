import streamlit as st
from docx import Document
import json
import os
import re
import atexit

PROGRESS_FILE = "progress.json"
# Đường dẫn tuyệt đối tới file .docx cùng thư mục với app.py
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
# Lưu / tải tiến trình
# --------------------
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "answers" not in data:
                data["answers"] = {}

            return data
        except:
            pass

    return {"answers": {}}


def save_progress(data):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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
    page_title="Quiz Game",
    page_icon="🎮",
    layout="wide"
)

st.title("🎮 Quiz Game từ File Word")


# --------------------
# Đọc file có sẵn trên repo
# --------------------
if not os.path.exists(DOCX_FILE):
    st.error(f"❌ Không tìm thấy file: {DOCX_FILE}")
    st.stop()

quiz = read_quiz(DOCX_FILE)
progress = load_progress()

st.success(f"📘 Đã đọc {len(quiz)} câu hỏi từ {DOCX_FILE}")


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
# Tùy chọn tự động xóa
# --------------------
auto_clear = st.sidebar.checkbox(
    "🧹 Tự động xóa tiến trình khi thoát app",
    value=False
)

if auto_clear:
    def clear_progress_on_exit():
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)

    atexit.register(clear_progress_on_exit)


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

        if selected:
            progress["answers"][key] = selected
        else:
            progress["answers"].pop(key, None)

        save_progress(progress)

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

        save_progress(progress)

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
if st.button("🗑️ Xóa tiến trình"):
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

    st.success("Đã xóa tiến trình! Hãy tải lại trang.")
