# python -m streamlit run myapp.py
import streamlit as st

# Set the title of the app
st.title("Welcome to the Streamlit App")

# Create a sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "About"])

# Load the appropriate page based on user selection
if page == "Home":
    st.write("This is the Home page.")
    # You can import and call the Home page functionality here
    # from pages.Home import display_home
    # display_home()
elif page == "About":
    st.write("This is the About page.")
    # You can import and call the About page functionality here
    # from pages.About import display_about
    # display_about()