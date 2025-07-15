import streamlit as st
import plotly.graph_objects as go
from utils import gen_real_pred_errors, calc_fairness_metrics

def fairness_analysis(df):
    st.markdown('<h1 class="main-header">Fairness</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:1.1rem;line-height:1.7;'>
    This page helps you check if the prediction model treats all NHS regions and BNF categories fairly.<br><br>
    1. How close the predictions are to the real values.<br>
    2. Whether predictions are too high or too low for some regions.<br>
    3. Whether all groups get similar results.<br><br>

    <span style='color:green;'><b>Green</b></span> means good (low error or bias). <span style='color:red;'><b>Red</b></span> means worse.<br>
    </div>
    """, unsafe_allow_html=True)
    df_errors = gen_real_pred_errors(df)
    if df_errors.empty:
        st.warning("Not enough data to compute real model fairness metrics. Please ensure there is sufficient historical data for each region and category.")
        return
    st.markdown("---")
    st.markdown("### Regional Fairness")
    st.markdown("We check if the model is equally accurate and unbiased for all regions. Lower error and bias are better.")
    regional_analysis(df_errors)
    st.markdown("---")

def regional_analysis(df_errors):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Accuracy by Region")
        st.caption("Shows the average prediction error for each region. Green is best, red is worst.")
        
        regional_mae = df_errors.groupby('REGIONAL_OFFICE_NAME')['MAE'].mean().sort_values()
        
        colors = ['green' if x < regional_mae.quantile(0.33) else
                  'orange' if x < regional_mae.quantile(0.67) else 'red'
                  for x in regional_mae.values]
        
        fig_accuracy = go.Figure(data=[
            go.Bar(
                y=regional_mae.index,
                x=regional_mae.values,
                orientation='h',
                marker=dict(color=colors),
                text=[f'£{val:.0f}' for val in regional_mae.values],
                textposition='outside'
            )
        ])
        
        fig_accuracy.update_layout(
            title="Mean Absolute Error by Region",
            xaxis_title="Mean Absolute Error (£)",
            yaxis_title="Region",
            height=500,
            template='plotly_white'
        )
        
        st.plotly_chart(fig_accuracy, use_container_width=True)
    
    with col2:
        st.subheader("Bias by Region")
        st.caption("Shows if predictions are too high (red) or too low (blue) for each region.")
        
        regional_bias = df_errors.groupby('REGIONAL_OFFICE_NAME')['Bias'].mean().sort_values()
        
        colors_bias = ['blue' if x < 0 else 'red' for x in regional_bias.values]
        
        fig_bias = go.Figure(data=[
            go.Bar(
                y=regional_bias.index,
                x=regional_bias.values,
                orientation='h',
                marker=dict(color=colors_bias),
                text=[f'£{val:.0f}' for val in regional_bias.values],
                textposition='outside'
            )
        ])
        
        fig_bias.add_vline(x=0, line=dict(color="black", width=2))
        
        fig_bias.update_layout(
            title="Prediction Bias by Region",
            xaxis_title="Prediction Bias (£)",
            yaxis_title="Region",
            height=500,
            template='plotly_white'
        )
        
        st.plotly_chart(fig_bias, use_container_width=True)

