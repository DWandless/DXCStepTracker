def plot_line_chart(data, title="Line Chart"):
    import streamlit as st
    import pandas as pd

    df = pd.DataFrame(data)
    st.line_chart(df)
    
def plot_bar_chart(data, title="Bar Chart"):
    import streamlit as st
    import pandas as pd

    df = pd.DataFrame(data)
    st.bar_chart(df)

def plot_area_chart(data, title="Area Chart"):
    import streamlit as st
    import pandas as pd

    df = pd.DataFrame(data)
    st.area_chart(df)