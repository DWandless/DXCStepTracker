# filepath: streamlit-app/pages/About.py
import streamlit as st

def about():
    st.title("About This Application")
    st.write("""
        This application is designed to help users track their steps during the Movember campaign.
        It provides insights into daily activity levels and encourages users to stay active.
        
        Features include:
        - Step tracking
        - Data visualization
        - User-friendly interface
        
        Thank you for participating in Movember and for using this application!
    """)

if __name__ == "__main__":
    about()