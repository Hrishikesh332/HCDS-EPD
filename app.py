import streamlit as st
from utils import load_data

from nav.dashboard import dashboard
from nav.forecasting import forecasting
from nav.fairness import fairness_analysis
from nav.outliers import outlier_analysis
from nav.clustering import clustering_analysis
from nav.categories import category_analysis

st.set_page_config(
    page_title="NHS Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 600;
        color: #1f77b4;
        margin-bottom: 1.5rem;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    
    .nav-bar {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }
    
    .insight-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    
    .alert-danger {
        background: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .alert-success {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'dashboard'
    df, data_type = load_and_cache_data()

    if data_type == "real":
        st.success("Successfully loaded NHS prescription data")
    else:
        st.warning("csv not found. Using sample data for demonstration.")

    create_nav()
    create_sidebar()
    route_to_page(df)

def create_nav():
    pages = {
        "Dashboard": "dashboard",
        "Forecast": "forecasting", 
        "Fairness": "fairness",
        "Anomaly": "outliers",
        "Grouping": "clustering",
        "Categories": "categories"
    }
    
    st.markdown('<div class="nav-bar">', unsafe_allow_html=True)
    cols = st.columns(len(pages))
    
    current_page = st.session_state.current_page
    
    for i, (page_name, page_key) in enumerate(pages.items()):
        with cols[i]:
            if st.button(
                page_name, 
                key=f"nav_{page_key}", 
                use_container_width=True,
                type="primary" if current_page == page_key else "secondary"
            ):
                st.session_state.current_page = page_key
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def create_sidebar():
    st.sidebar.title("")
    st.sidebar.markdown("")
    
    pages = {
        "Dashboard": "dashboard",
        "Forecast": "forecasting", 
        "Fairness": "fairness",
        "Anomaly": "outliers",
        "Grouping": "clustering",
        "Categories": "categories"
    }
    
    current_page = st.session_state.current_page
    
    for page_name, page_key in pages.items():
        if st.sidebar.button(
            page_name, 
            key=f"sidebar_{page_key}", 
            use_container_width=True,
            type="primary" if current_page == page_key else "secondary"
        ):
            st.session_state.current_page = page_key
            st.rerun()

@st.cache_data
def load_and_cache_data():
    return load_data()

def route_to_page(df):
    current_page = st.session_state.current_page
    
    try:
        if current_page == "dashboard":
            dashboard(df)
        elif current_page == "forecasting":
            forecasting(df)
        elif current_page == "fairness":
            fairness_analysis(df)
        elif current_page == "outliers":
            outlier_analysis(df)
        elif current_page == "clustering":
            clustering_analysis(df)
        elif current_page == "categories":
            category_analysis(df)
        else:
            st.error(f"Unknown page: {current_page}")
            dashboard(df)
            
    except Exception as e:
        st.error(f"Error loading page '{current_page}': {str(e)}")
        st.info("Falling back to dashboard.")
        dashboard(df)

if __name__ == "__main__":
    main()