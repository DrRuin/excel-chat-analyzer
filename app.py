import streamlit as st
import httpx
import json
import uuid
from streamlit_gpt_vis import set_gpt_vis

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Excel Analyzer", layout="wide")
st.title("Excel Financial Analyzer")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "file_uploaded" not in st.session_state:
    st.session_state.file_uploaded = False
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# Sidebar
with st.sidebar:
    st.header("Upload Data")
    uploaded_file = st.file_uploader("Choose Excel or CSV", type=["xlsx", "xls", "csv"])

    if uploaded_file and not st.session_state.file_uploaded:
        with st.spinner("Uploading..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            response = httpx.post(f"{API_URL}/upload", files=files, timeout=30)

            if response.status_code == 200:
                data = response.json()
                st.session_state.file_uploaded = True
                st.session_state.file_info = data
                st.success(f"Uploaded: {data['filename']}")
            else:
                st.error(response.json().get("detail", "Upload failed"))

    if st.session_state.file_uploaded:
        info = st.session_state.file_info
        st.write(f"**Rows:** {info['rows']}")
        st.write(f"**Columns:** {', '.join(info['columns'])}")

        if st.button("Clear Data"):
            st.session_state.file_uploaded = False
            st.session_state.messages = []
            st.session_state.thread_id = str(uuid.uuid4())
            st.rerun()

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            if "steps" in msg and msg["steps"]:
                with st.expander("🔧 Steps", expanded=False):
                    for step in msg["steps"]:
                        st.markdown(step)
            set_gpt_vis(msg["content"])
        else:
            st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask about your data..."):
    if not st.session_state.file_uploaded:
        st.warning("Please upload a file first.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            steps_container = st.empty()
            response_container = st.empty()

            steps = []
            response_text = ""

            try:
                with httpx.stream(
                    "POST",
                    f"{API_URL}/query/stream",
                    json={"query": prompt, "thread_id": st.session_state.thread_id},
                    timeout=120,
                ) as response:
                    for line in response.iter_lines():
                        if line.startswith("data: "):
                            data = json.loads(line[6:])

                            if data["type"] == "tool_start":
                                step = f"🔄 **Using:** `{data['tool']}`"
                                steps.append(step)
                                with steps_container.expander(
                                    "🔧 Steps", expanded=True
                                ):
                                    for s in steps:
                                        st.markdown(s)

                            elif data["type"] == "tool_end":
                                step = f"✅ **{data['tool']}** completed"
                                steps.append(step)
                                with steps_container.expander(
                                    "🔧 Steps", expanded=True
                                ):
                                    for s in steps:
                                        st.markdown(s)

                            elif data["type"] == "token":
                                response_text += data["content"]
                                response_container.markdown(response_text + "▌")

                            elif data["type"] == "done":
                                pass

                # Render final response with GPT-Vis charts
                response_container.empty()
                set_gpt_vis(response_text)

                st.session_state.messages.append(
                    {"role": "assistant", "content": response_text, "steps": steps}
                )

            except httpx.TimeoutException:
                st.error("Request timed out.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
