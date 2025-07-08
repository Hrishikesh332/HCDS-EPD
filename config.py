import streamlit as st

def create_region_selector(df):
    regions = sorted(df['REGIONAL_OFFICE_NAME'].unique())
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_region = st.selectbox(
            "Select NHS Region",
            regions,
            key="region_selector"
        )
    
    with col2:
        st.metric("Total Regions", len(regions))
    
    return selected_region