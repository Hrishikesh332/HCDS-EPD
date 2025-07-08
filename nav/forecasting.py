import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils import train_arima
from config import create_region_selector

def forecasting(df):
    st.markdown('<h1 class="main-header">Forecast</h1>', unsafe_allow_html=True)
    
    selected_region = create_region_selector(df)
    region_data = df[df['REGIONAL_OFFICE_NAME'] == selected_region]
    available_categories = sorted(region_data['BNF_CHAPTER_PLUS_CODE'].unique())
    default_categories = available_categories[:8] if len(available_categories) > 8 else available_categories
    selected_categories = st.multiselect(
        "Choose Categories:",
        available_categories,
        default=default_categories
    )
    
    col1, _ = st.columns(2)
    with col1:
        forecast_periods = st.slider("Months to Forecast:", 1, 12, 3)
    
    if not selected_categories:
        st.warning("Select at least one category.")
        return
    
    line_chart = create_multi_category_forecast(region_data, selected_categories, forecast_periods)
    st.plotly_chart(line_chart, use_container_width=True)
    
    forecast_insights(region_data, selected_categories, forecast_periods)

def create_multi_category_forecast(region_data, selected_categories, forecast_months):
    all_bnf = region_data.groupby('BNF_CHAPTER_PLUS_CODE')['TOTAL_COST'].sum()
    
    fig = go.Figure()
    
    historical_colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD',
        '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9', '#F8C471', '#82E0AA',
        '#F1948A', '#85C1E9', '#D7BDE2', '#A9CCE3', '#FAD7A0', '#ABEBC6',
        '#F5B7B1', '#AED6F1', '#D5A6BD', '#A2D9CE', '#F9E79F', '#D2B4DE'
    ]
    
    forecast_colors = [
        '#FF8E8E', '#6EDDD6', '#65C7E1', '#A6DEB4', '#FFF2B7', '#EDB0ED',
        '#A8E8D8', '#F7EC7F', '#CB9FDE', '#95D1F9', '#F8D481', '#92F0BA',
        '#F1A49A', '#95D1F9', '#E7CDE2', '#B9DCE3', '#FAE7B0', '#BBEBD6',
        '#F5C7C1', '#BEE6F1', '#E5B6CD', '#B2E9DE', '#F9F79F', '#E2C4EE'
    ]
    
    forecast_start_date = None
    all_dates = []
    all_categories_data = {}
    failed_categories = []
    filtered_bnf = [bnf for bnf in all_bnf.index if bnf in selected_categories]
    for i, bnf_code in enumerate(filtered_bnf):
        bnf_data = region_data[region_data['BNF_CHAPTER_PLUS_CODE'] == bnf_code]
        ts_data = bnf_data.groupby('YEAR_MONTH')['TOTAL_COST'].sum().reset_index()
        
        if len(ts_data) >= 3:
            category_parts = bnf_code.split(":")
            if len(category_parts) >= 2:
                category_short = f"{category_parts[0].strip()}: {category_parts[1].strip()}"
            else:
                category_short = bnf_code.strip()
            
            try:
                forecast_df = train_arima(ts_data, forecast_months)
                
                if forecast_start_date is None:
                    forecast_start_date = forecast_df['YEAR_MONTH'].iloc[0]
                
                combined_dates = list(ts_data['YEAR_MONTH']) + list(forecast_df['YEAR_MONTH'])
                combined_values = list(ts_data['TOTAL_COST']) + list(forecast_df['FORECAST'])
                
                all_dates.extend(combined_dates)
                all_categories_data[category_short] = {
                    'dates': combined_dates,
                    'values': combined_values,
                    'historical_end': len(ts_data) - 1,
                    'historical_color': historical_colors[i % len(historical_colors)],
                    'forecast_color': forecast_colors[i % len(forecast_colors)]
                }
            except ValueError as e:
                failed_categories.append(category_short)
                continue
    
    if failed_categories:
        st.warning(f"ARIMA modeling failed for {len(failed_categories)} categories: {', '.join(failed_categories[:5])}{'...' if len(failed_categories) > 5 else ''}")
    
    if all_categories_data:
        unique_dates = sorted(set(all_dates))
        
        for category, data in all_categories_data.items():
            historical_dates = data['dates'][:data['historical_end'] + 1]
            historical_values = data['values'][:data['historical_end'] + 1]
            
            forecast_dates = data['dates'][data['historical_end']:]
            forecast_values = data['values'][data['historical_end']:]
            
            fig.add_trace(go.Scatter(
                x=historical_dates,
                y=historical_values,
                mode='none',
                fill='tonexty' if len(fig.data) > 0 else 'tozeroy',
                name=category,
                fillcolor=data['historical_color'],
                line=dict(width=0),
                stackgroup='historical',
                hovertemplate=f'<b>{category}</b><br>%{{x}}<br>Cost: £%{{y:,.0f}}<extra></extra>',
                showlegend=True
            ))
            
            fig.add_trace(go.Scatter(
                x=forecast_dates,
                y=forecast_values,
                mode='none',
                fill='tonexty' if len([t for t in fig.data if 'Forecast' in t.name]) > 0 else 'tozeroy',
                name=f'{category} (Forecast)',
                fillcolor=data['forecast_color'],
                line=dict(width=0, dash='dash'),
                stackgroup='forecast',
                hovertemplate=f'<b>{category} Forecast</b><br>%{{x}}<br>Forecast: £%{{y:,.0f}}<extra></extra>',
                showlegend=True
            ))
    
    if forecast_start_date:
        fig.add_shape(
            type="line",
            x0=forecast_start_date,
            x1=forecast_start_date,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color="#E74C3C", width=3, dash="dot")
        )
        
        fig.add_annotation(
            x=forecast_start_date,
            y=1.05,
            yref="paper",
            text="Forecast Start",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#E74C3C",
            font=dict(size=12, color="#E74C3C"),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#E74C3C",
            borderwidth=1
        )
    
    fig.update_layout(
        title=dict(
            text=f'Prescription Forecast - {region_data["REGIONAL_OFFICE_NAME"].iloc[0] if len(region_data) > 0 else ""}',
            font=dict(size=20, color='#2C3E50')
        ),
        xaxis_title='Date',
        yaxis_title='Total Cost (£)',
        height=700,
        showlegend=True,
        hovermode='x unified',
        template='plotly_white',
        plot_bgcolor='rgba(248, 249, 250, 0.9)',
        paper_bgcolor='rgba(255, 255, 255, 1)',
        legend=dict(
            orientation="v",
            yanchor="top", 
            y=1,
            xanchor="left",
            x=1.02,
            title=dict(text="BNF Categories", font=dict(size=14, color='#2C3E50')),
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
            font=dict(size=11, color='#2C3E50')
        ),
        margin=dict(r=220, t=80, l=80, b=80),
        xaxis=dict(
            showgrid=True, 
            gridwidth=1, 
            gridcolor='rgba(200, 200, 200, 0.4)',
            zeroline=False,
            title_font=dict(size=14, color='#2C3E50'),
            tickfont=dict(size=12, color='#2C3E50')
        ),
        yaxis=dict(
            showgrid=True, 
            gridwidth=1, 
            gridcolor='rgba(200, 200, 200, 0.4)',
            zeroline=False,
            title_font=dict(size=14, color='#2C3E50'),
            tickfont=dict(size=12, color='#2C3E50')
        )
    )
    
    return fig

def forecast_insights(region_data, selected_categories, forecast_periods):

    ts_data = region_data.groupby('YEAR_MONTH')['TOTAL_COST'].sum().reset_index()
    
    if len(ts_data) >= 3:
        try:
            forecast_df = train_arima(ts_data, forecast_periods)
            
            if len(forecast_df) > 0:
                forecast_accuracy_metrics(ts_data, forecast_periods)
        except ValueError as e:
            st.error(f"ARIMA modeling failed: {str(e)}")

def forecast_accuracy_metrics(ts_data, forecast_periods):
    st.subheader("Model Performance Metrics")
    
    if len(ts_data) >= 12:
        train_size = len(ts_data) - forecast_periods
        train_data = ts_data.iloc[:train_size]
        test_data = ts_data.iloc[train_size:]
        
        if len(train_data) >= 3 and len(test_data) > 0:
            try:
                forecast_df = train_arima(train_data, len(test_data))
                
                if len(forecast_df) > 0 and len(test_data) == len(forecast_df):
                    mae = abs(test_data['TOTAL_COST'].values - forecast_df['FORECAST'].values).mean()
                    mape = (abs(test_data['TOTAL_COST'].values - forecast_df['FORECAST'].values) / 
                           test_data['TOTAL_COST'].values * 100).mean()
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Mean Absolute Error", f"£{mae:,.0f}")
                    
                    with col2:
                        st.metric("Mean Absolute Percentage Error", f"{mape:.1f}%")
                    
                    with col3:
                        accuracy = max(0, 100 - mape)
                        st.metric("Model Accuracy", f"{accuracy:.1f}%")
            except ValueError as e:
                st.error(f"Model performance evaluation failed: {str(e)}")