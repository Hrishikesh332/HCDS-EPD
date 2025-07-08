import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils import detect_outliers

def outlier_analysis(df):
    st.markdown('<h1 class="main-header">Outliers</h1>', unsafe_allow_html=True)
    st.markdown("""
    This page helps you find unusual (outlier) prescription costs in NHS data. We use the Isolation Forest method to automatically spot outliers. Outliers can show errors or important changes in patterns.
    """)
    configure_detection_parameters(df)

def configure_detection_parameters(df):
    st.markdown("**Outliers are detected using the Isolation Forest method.**")
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
        st.info(f"Data from {start_date} to {end_date} ({len(df_filtered):,} records)")
    else:
        df_filtered = df
        st.info(f"All data ({len(df_filtered):,} records)")
    if len(df_filtered) == 0:
        st.error("No data available for the selected date range. Please adjust your filters.")
        return
    # Use only Isolation Forest, with default parameters
    detection_method = "Isolation Forest"
    threshold = 1.5  # default, not shown
    contamination = 0.1  # default, not shown
    regional_outlier_analysis(df_filtered, detection_method, threshold, contamination)


def regional_outlier_analysis(df, detection_method, threshold, contamination):
    try:
        regional_outliers = detect_outliers(df, detection_method, threshold, contamination, 'regional')
        # Only show the Outlier % by Region plot and stats, not the boxplot
        st.markdown("**Note: Outliers are detected using the Isolation Forest method.**")
        if len(regional_outliers) > 0:
            st.subheader("Outlier % by Region")
            st.caption("Shows what percent of data in each region are outliers.")
            regional_outlier_counts = regional_outliers.groupby('REGIONAL_OFFICE_NAME').size()
            regional_total_counts = df.groupby('REGIONAL_OFFICE_NAME').size()
            outlier_intensity = (regional_outlier_counts / regional_total_counts * 100).fillna(0)
            if len(outlier_intensity) > 0:
                import plotly.express as px
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
            st.subheader("No Outliers")
            st.info("No outliers found. Try changing the date range.")
        outlier_analytics(df, regional_outliers)
    except Exception as e:
        st.error(f"Error: {str(e)}")

def outlier_analytics(df, regional_outliers):
    st.subheader("Outlier Stats")
    st.caption("Quick summary of outlier numbers and costs.")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total", len(regional_outliers))
    
    with col2:
        percentage = (len(regional_outliers)/len(df)*100) if len(df) > 0 else 0
        st.metric("% of Data", f"{percentage:.2f}%")
    
    with col3:
        if len(regional_outliers) > 0:
            median_cost = regional_outliers['TOTAL_COST'].median()
            st.metric("Median Cost", f"\u00a3{median_cost:,.0f}")
        else:
            st.metric("Median Cost", "N/A")
    
    with col4:
        if len(regional_outliers) > 0:
            max_cost = regional_outliers['TOTAL_COST'].max()
            st.metric("Max Cost", f"\u00a3{max_cost:,.0f}")
        else:
            st.metric("Max Cost", "N/A")
    
    if len(regional_outliers) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Top Regions")
            st.caption("These regions have the most detected outliers.")
            top_outlier_regions = regional_outliers['REGIONAL_OFFICE_NAME'].value_counts().head(5)
            for region, count in top_outlier_regions.items():
                st.write(f"• **{region}** - {count} outliers")
        
        with col2:
            st.subheader("Top 5 Outliers")
            st.caption("These are the 5 highest-cost outlier records found.")
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

