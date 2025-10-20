import streamlit as st

def main():
    st.title("Welcome to the Home Page")
    st.write("This is the home page of the Streamlit application.")
    st.write("Here you can find an overview of the app's features and functionalities.")
    
    # Add more components and layout as needed
    st.image("path/to/image.png", caption="Sample Image")  # Example of adding an image
    st.button("Click Me")  # Example of adding a button

if __name__ == "__main__":
    main()