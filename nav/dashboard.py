import streamlit as st
import plotly.express as px
from utils import create_map
from config import create_region_selector

def dashboard(df):
    st.markdown('<h1 class="main-header">NHS Prescription Analytics Dashboard</h1>', unsafe_allow_html=True)
    
    selected_region = create_region_selector(df)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Regional Cost Distribution")
        map_fig = create_map(df, selected_region)
        st.plotly_chart(map_fig, use_container_width=True)
    
    with col2:
        st.subheader("Key Performance Indicators")
        
        region_data = df[df['REGIONAL_OFFICE_NAME'] == selected_region]
        total_cost = region_data['TOTAL_COST'].sum()
        monthly_avg = region_data.groupby('YEAR_MONTH')['TOTAL_COST'].sum().mean()
        
        st.metric("Total Cost", f"£{total_cost:,.0f}")
        st.metric("Monthly Average", f"£{monthly_avg:,.0f}")
        
        region_totals = df.groupby('REGIONAL_OFFICE_NAME')['TOTAL_COST'].sum()
        rank = region_totals.rank(ascending=False)[selected_region]
        st.metric("National Ranking", f"#{rank:.0f}")
        
        market_share = (total_cost / df['TOTAL_COST'].sum()) * 100
        st.metric("Market Share", f"{market_share:.1f}%")
    
    st.markdown("---")
    
    st.subheader("Regional Cost Comparison")
    region_totals = df.groupby('REGIONAL_OFFICE_NAME')['TOTAL_COST'].sum().sort_values(ascending=True)
    
    colors = ['#FF6B6B' if region == selected_region else '#4ECDC4' for region in region_totals.index]
    
    fig = px.bar(
        x=region_totals.values,
        y=region_totals.index,
        orientation='h',
        title="Total NHS Prescription Costs by Region",
        labels={'x': 'Total Cost (£)', 'y': 'Region'},
        color=region_totals.index,
        color_discrete_sequence=colors,
        text=region_totals.values
    )
    
    fig.update_traces(texttemplate='£%{text:,.0f}', textposition='outside')
    fig.update_layout(
        height=400,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'},
        margin={'l': 180},
        template='plotly_white'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    time_series_overview(df)

def time_series_overview(df):
    st.subheader("Monthly Prescription Trends")
    
    monthly_totals = df.groupby('YEAR_MONTH')['TOTAL_COST'].sum().reset_index()

    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_cost_all = df['TOTAL_COST'].sum()
        st.metric("Total Dataset Cost", f"£{total_cost_all:,.0f}")
    
    with col2:
        avg_monthly = monthly_totals['TOTAL_COST'].mean()
        st.metric("Average Monthly Cost", f"£{avg_monthly:,.0f}")
    
    with col3:
        growth_rate = ((monthly_totals['TOTAL_COST'].iloc[-1] - monthly_totals['TOTAL_COST'].iloc[0]) / 
                      monthly_totals['TOTAL_COST'].iloc[0] * 100)
        st.metric("Overall Growth Rate", f"{growth_rate:.1f}%")
    
    fig = px.line(
        monthly_totals,
        x='YEAR_MONTH',
        y='TOTAL_COST',
        title="Total Monthly NHS Prescription Costs",
        labels={'TOTAL_COST': 'Total Cost (£)', 'YEAR_MONTH': 'Date'}
    )
    
    fig.update_traces(line=dict(width=3, color='#1f77b4'))
    fig.update_layout(
        height=400,
        template='plotly_white',
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
