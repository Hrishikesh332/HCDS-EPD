import streamlit as st
import plotly.graph_objects as go
from utils import gen_real_pred_errors, calc_fairness_metrics

def fairness_analysis(df):
    st.markdown('<h1 class="main-header">Fairness Analysis</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    Fairness of prediction models across different NHS regions and BNF categories.
    """)
    
    df_errors = gen_real_pred_errors(df)
    if df_errors.empty:
        st.warning("Not enough data to compute real model fairness metrics. Please ensure there is sufficient historical data for each region and category.")
        return
    fairness_results = calc_fairness_metrics(df_errors)
    
    regional_analysis(df_errors)
    statistical_tests(fairness_results)

def regional_analysis(df_errors):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Regional Prediction Accuracy")
        
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
        st.subheader("Regional Prediction Bias")
        
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

def bnf_performance(df_errors):
    st.subheader("BNF Category Performance Analysis")
    
    bnf_mae_stats = df_errors.groupby('BNF_CATEGORY').agg({'MAE': ['mean', 'count']}).round(2)
    bnf_mae_stats.columns = ['MAE_Mean', 'Count']
    top_bnf = bnf_mae_stats[bnf_mae_stats['Count'] >= 5].sort_values('MAE_Mean', ascending=False).head(10)
    
    if len(top_bnf) > 0:
        fig_bnf = go.Figure(data=[
            go.Bar(
                y=[f'BNF {idx} ({count} regions)' for idx, count in zip(top_bnf.index, top_bnf['Count'])],
                x=top_bnf['MAE_Mean'].values,
                orientation='h',
                marker=dict(
                    color=top_bnf['MAE_Mean'].values,
                    colorscale='viridis',
                    showscale=True,
                    colorbar=dict(title="Mean Absolute Error")
                ),
                text=[f'{val:.0f}' for val in top_bnf['MAE_Mean'].values],
                textposition='outside'
            )
        ])
        
        fig_bnf.update_layout(
            title="BNF Category Performance",
            xaxis_title="Mean Absolute Error (£)",
            yaxis_title="BNF Category",
            height=500,
            template='plotly_white'
        )
        
        st.plotly_chart(fig_bnf, use_container_width=True)

def statistical_tests(fairness_results):
    st.subheader("Statistical Fairness Tests")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Statistical Test Results**")
        tests = fairness_results['statistical_tests']
        parity_df = fairness_results['parity_df']
        parity_gap = fairness_results['parity_gap']
        
        st.write(f"**Bias across regions (F-test):** F = {tests['f_stat_bias']:.4f}, p = {tests['p_val_bias']:.2e}")
        st.write(f"**MAE across regions (Kruskal-Wallis):** H = {tests['kw_stat_mae']:.4f}, p = {tests['kw_p_mae']:.2e}")
        st.write(f"**Bias across regions (Kruskal-Wallis):** H = {tests['kw_stat_bias']:.4f}, p = {tests['kw_p_bias']:.2e}")
        
        if tests['p_val_bias'] < 0.05:
            st.markdown('<div class="alert-danger"><strong>Alert - </strong> Significant bias differences detected across regions</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-success"><strong>Good - </strong> No significant bias differences across regions</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("**Parity Analysis**")
        
        st.dataframe(parity_df.round(4), use_container_width=True, hide_index=True)
        
        st.metric("Parity Gap", f"{parity_gap:.4f}")
        
        if parity_gap > 0.1:
            st.markdown('<div class="alert-danger"><strong>Concern - </strong> Large parity gap detected</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-success"><strong>Good - </strong> Acceptable parity levels</div>', unsafe_allow_html=True)

