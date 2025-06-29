import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils import detect_outliers

def outlier_analysis(df):
    st.markdown('<h1 class="main-header">Outlier Detection Analysis</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    Outlier detection using multiple statistical methods to identify anomalous 
    prescription patterns across regions, time periods, and therapeutic categories.
    """)
    
    configure_detection_parameters(df)

def configure_detection_parameters(df):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        detection_method = st.selectbox(
            "Detection Method",
            ["IQR Method", "Isolation Forest"]
        )
    
    with col2:
        analysis_level = st.selectbox(
            "Analysis Level",
            ["Regional Analysis"]
        )
    
    with col3:
        threshold = st.slider("Sensitivity:", 0.1, 3.0, 1.5, 0.1)
    
    with col4:
        contamination = st.slider("Expected Outlier %:", 0.01, 0.25, 0.1, 0.01)
    
    min_date = df['YEAR_MONTH'].min().date()
    max_date = df['YEAR_MONTH'].max().date()
    
    outlier_date_range = st.date_input(
        "Analysis Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if len(outlier_date_range) == 2:
        start_date, end_date = outlier_date_range
        df_filtered = df[(df['YEAR_MONTH'].dt.date >= start_date) & (df['YEAR_MONTH'].dt.date <= end_date)]
        st.info(f"Analyzing data from {start_date} to {end_date} ({len(df_filtered):,} records)")
    else:
        df_filtered = df
        st.info(f"Analyzing complete dataset ({len(df_filtered):,} records)")
    
    if len(df_filtered) == 0:
        st.error("No data available for the selected date range. Please adjust your filters.")
        return
    
    
    try:
        if analysis_level == "Regional Analysis":
            regional_outlier_analysis(df_filtered, detection_method, threshold, contamination)

    
    except Exception as e:
        st.error(f"An error occurred during outlier analysis: {str(e)}")
        st.info("Please try adjusting the parameters or check your data filters.")


def regional_outlier_analysis(df, detection_method, threshold, contamination):
    try:
        regional_outliers = detect_outliers(df, detection_method, threshold, contamination, 'regional')
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Regional Outlier Distribution")
            
            fig = px.box(
                df, 
                x='REGIONAL_OFFICE_NAME', 
                y='TOTAL_COST',
                title="Regional Cost Distribution with Outliers",
                labels={'TOTAL_COST': 'Total Cost (£)', 'REGIONAL_OFFICE_NAME': 'Region'}
            )
            fig.update_layout(xaxis={'tickangle': 45}, height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if len(regional_outliers) > 0:
                st.subheader("Outlier Intensity by Region")
                regional_outlier_counts = regional_outliers.groupby('REGIONAL_OFFICE_NAME').size()
                regional_total_counts = df.groupby('REGIONAL_OFFICE_NAME').size()
                outlier_intensity = (regional_outlier_counts / regional_total_counts * 100).fillna(0)
                
                if len(outlier_intensity) > 0:
                    fig_heatmap = px.bar(
                        x=outlier_intensity.index,
                        y=outlier_intensity.values,
                        title="Outlier Percentage by Region",
                        labels={'x': 'Region', 'y': 'Outlier Percentage (%)'},
                        color=outlier_intensity.values,
                        color_continuous_scale='Reds'
                    )
                    fig_heatmap.update_layout(xaxis={'tickangle': 45}, height=500)
                    st.plotly_chart(fig_heatmap, use_container_width=True)
            else:
                st.subheader("No Outliers Detected")
                st.info("No outliers detected with current parameters. Try adjusting the sensitivity.")
        
        outlier_analytics(df, regional_outliers)
    
    except Exception as e:
        st.error(f"Error in regional outlier analysis: {str(e)}")

def outlier_analytics(df, regional_outliers):
    st.subheader("Outlier Analytics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Outliers", len(regional_outliers))
    
    with col2:
        percentage = (len(regional_outliers)/len(df)*100) if len(df) > 0 else 0
        st.metric("% of Total Data", f"{percentage:.2f}%")
    
    with col3:
        if len(regional_outliers) > 0:
            median_cost = regional_outliers['TOTAL_COST'].median()
            st.metric("Median Outlier Cost", f"£{median_cost:,.0f}")
        else:
            st.metric("Median Outlier Cost", "N/A")
    
    with col4:
        if len(regional_outliers) > 0:
            max_cost = regional_outliers['TOTAL_COST'].max()
            st.metric("Highest Outlier Cost", f"£{max_cost:,.0f}")
        else:
            st.metric("Highest Outlier Cost", "N/A")
    
    if len(regional_outliers) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Top Outlier Regions")
            top_outlier_regions = regional_outliers['REGIONAL_OFFICE_NAME'].value_counts().head(5)
            for region, count in top_outlier_regions.items():
                st.write(f"• **{region}** - {count} outliers")
        
        with col2:
            st.subheader("[TOP 5] High-Cost Outliers")
            outlier_sample = regional_outliers.nlargest(5, 'TOTAL_COST')[
                ['YEAR_MONTH', 'REGIONAL_OFFICE_NAME', 'BNF_CHAPTER_PLUS_CODE', 'TOTAL_COST']
            ]
            if len(outlier_sample) > 0:
                outlier_sample_display = outlier_sample.copy()
                outlier_sample_display['TOTAL_COST'] = outlier_sample_display['TOTAL_COST'].apply(lambda x: f"£{x:,.0f}")
                outlier_sample_display['YEAR_MONTH'] = outlier_sample_display['YEAR_MONTH'].dt.strftime('%Y-%m')
                st.dataframe(outlier_sample_display, use_container_width=True, hide_index=True)
    else:
        pass

