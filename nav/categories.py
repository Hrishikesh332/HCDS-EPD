import streamlit as st
import pandas as pd
import plotly.express as px

def category_analysis(df):
    st.markdown('<h1 class="main-header">Categories</h1>', unsafe_allow_html=True)
    st.markdown("")
    
    available_categories = sorted(df['BNF_CHAPTER_PLUS_CODE'].unique())
    
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_categories = st.multiselect(
            "Choose Categories:",
            available_categories,
            default=list(available_categories)[:5]
        )
    
    with col2:
        st.metric("Available", len(available_categories))
        if selected_categories:
            st.metric("Chosen", len(selected_categories))
    
    if not selected_categories:
        st.warning("Select at least one category.")
        return
    
    filtered_df = df[df['BNF_CHAPTER_PLUS_CODE'].isin(selected_categories)]
    category_totals = filtered_df.groupby('BNF_CHAPTER_PLUS_CODE')['TOTAL_COST'].sum().sort_values(ascending=False)
    
    category_overview(filtered_df, category_totals)
    category_trends(filtered_df, category_totals, selected_categories)
    

def category_overview(filtered_df, category_totals):
    st.subheader("Overview")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Total by Category**")
        fig_bar = px.bar(
            x=category_totals.values,
            y=[cat.split(':')[0] + ": " + cat.split(':')[1].strip() if ':' in cat else cat for cat in category_totals.index],
            orientation='h',
            title="BNF Category Total Costs",
            labels={'x': 'Total Cost (£)', 'y': 'BNF Category'},
            color=category_totals.values,
            color_continuous_scale='Blues',
            text=category_totals.values,
            height=max(400, len(category_totals) * 50)
        )
        
        fig_bar.update_traces(texttemplate='£%{text:,.0f}', textposition='outside')
        fig_bar.update_layout(
            showlegend=False,
            margin={'l': 250},
            template='plotly_white'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        st.markdown("Numbers")
        total_cost = filtered_df['TOTAL_COST'].sum()
        avg_cost = filtered_df['TOTAL_COST'].mean()
        total_records = len(filtered_df)
        top_category = category_totals.index[0].split(':')[0] if len(category_totals) > 0 else "N/A"
        
        st.metric("Total", f"\u00a3{total_cost:,.0f}")
        st.metric("Average", f"\u00a3{avg_cost:,.0f}")
        st.metric("Records", f"{total_records:,}")

def category_trends(filtered_df, category_totals, selected_categories):
    st.subheader("Trends Over Time")
    
    time_category = filtered_df.groupby(['YEAR_MONTH', 'BNF_CHAPTER_PLUS_CODE'])['TOTAL_COST'].sum().reset_index()
    
    st.markdown("**Over Time**")
    top_categories_for_trends = category_totals.head(min(8, len(selected_categories))).index
    time_category_filtered = time_category[time_category['BNF_CHAPTER_PLUS_CODE'].isin(top_categories_for_trends)]
    
    if len(time_category_filtered) > 0:
        fig_time = px.line(
            time_category_filtered,
            x='YEAR_MONTH',
            y='TOTAL_COST',
            color='BNF_CHAPTER_PLUS_CODE',
            title=f"Top {len(top_categories_for_trends)} Category Costs Over Time",
            labels={'TOTAL_COST': 'Total Cost (£)', 'YEAR_MONTH': 'Date'},
            color_discrete_sequence=['#AED6F1', '#F9E79F', '#ABEBC6', '#F5B7B1', '#D2B4DE', '#F0B27A', '#A9DFBF', '#D5DBDB']
        )
        
        fig_time.update_layout(
            height=500,
            legend_title="BNF Categories",
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
            margin=dict(r=200)
        )
        
        fig_time.update_traces(line=dict(width=3), marker=dict(size=6))
        st.plotly_chart(fig_time, use_container_width=True)
    
    st.subheader("Seasonal & Annual")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Monthly Patterns**")
        if len(time_category_filtered) > 0:
            time_category_filtered_copy = time_category_filtered.copy()
            time_category_filtered_copy['Month'] = time_category_filtered_copy['YEAR_MONTH'].dt.month
            monthly_avg = time_category_filtered_copy.groupby(['Month', 'BNF_CHAPTER_PLUS_CODE'])['TOTAL_COST'].mean().reset_index()
            
            fig_seasonal = px.line(
                monthly_avg,
                x='Month',
                y='TOTAL_COST',
                color='BNF_CHAPTER_PLUS_CODE',
                title="Average Monthly Costs by Category",
                labels={'TOTAL_COST': 'Average Cost (£)', 'Month': 'Month'},
                color_discrete_sequence=['#AED6F1', '#F9E79F', '#ABEBC6', '#F5B7B1', '#D2B4DE', '#F0B27A']
            )
            
            fig_seasonal.update_layout(
                height=400,
                xaxis=dict(tickmode='linear', tick0=1, dtick=1)
            )
            
            st.plotly_chart(fig_seasonal, use_container_width=True)
    
    with col2:
        st.markdown("**Annual Trends**")
        if len(time_category_filtered) > 0:
            time_category_filtered_copy = time_category_filtered.copy()
            time_category_filtered_copy['Year'] = time_category_filtered_copy['YEAR_MONTH'].dt.year
            yearly_totals = time_category_filtered_copy.groupby(['Year', 'BNF_CHAPTER_PLUS_CODE'])['TOTAL_COST'].sum().reset_index()
            
            fig_yearly = px.bar(
                yearly_totals,
                x='Year',
                y='TOTAL_COST',
                color='BNF_CHAPTER_PLUS_CODE',
                title="Annual Costs by Category",
                labels={'TOTAL_COST': 'Total Cost (£)', 'Year': 'Year'},
                color_discrete_sequence=['#AED6F1', '#F9E79F', '#ABEBC6', '#F5B7B1', '#D2B4DE', '#F0B27A']
            )
            
            fig_yearly.update_layout(height=400)
            st.plotly_chart(fig_yearly, use_container_width=True)
