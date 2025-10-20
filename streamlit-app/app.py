import streamlit as st

st.set_page_config(page_title="Movember Step Tracker", layout="wide")

st.title("Movember Step Tracker")
st.write(
    "This app uses Streamlit's built-in Pages menu. Open the Pages menu (top-left ⋮ / left sidebar) "
    "and choose Home, About or Protected."
)

# show logged-in user if Protected page set it
if st.session_state.get("username"):
    st.sidebar.markdown(f"**User:** {st.session_state.get('username')}")
