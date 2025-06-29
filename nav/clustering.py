import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import AgglomerativeClustering
from utils import REGION_COORDINATES

def clustering_analysis(df):
    st.markdown('<h1 class="main-header">Regional Clustering Analysis</h1>', unsafe_allow_html=True)
    
    n_clusters = st.slider("Number of Clusters", 2, 6, 3)
    
    try:
        regional_clustering(df, n_clusters)
    except Exception as e:
        st.error(f"Error in clustering analysis: {str(e)}")

def regional_clustering(df, n_clusters):
    try:
        regional_features = df.groupby('REGIONAL_OFFICE_NAME').agg({
            'TOTAL_COST': ['sum', 'mean', 'std', 'count']
        }).round(2)
        regional_features.columns = ['Total_Cost', 'Mean_Cost', 'Std_Cost', 'Record_Count']
        regional_features = regional_features.reset_index()
        
        regional_features['Cost_Per_Record'] = regional_features['Total_Cost'] / regional_features['Record_Count']
        regional_features['Cost_Variability'] = regional_features['Std_Cost'] / regional_features['Mean_Cost']
        regional_features = regional_features.fillna(0)
        
        feature_cols = ['Total_Cost', 'Mean_Cost', 'Cost_Variability', 'Cost_Per_Record']
        X = regional_features[feature_cols].fillna(0)
        
        if len(X) > 0 and X.std().sum() > 0:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            clusterer = AgglomerativeClustering(n_clusters=n_clusters)
            cluster_labels = clusterer.fit_predict(X_scaled)
            regional_features['Cluster'] = cluster_labels.astype(str)
            
            cluster_overview(regional_features)
            cluster_visualization(regional_features, X_scaled, feature_cols)
            geographic_distribution(regional_features)
            cluster_details(regional_features, feature_cols)
            
        else:
            st.info("Insufficient data variation for clustering analysis")
    
    except Exception as e:
        st.error(f"Error in regional clustering: {str(e)}")

def cluster_overview(regional_features):
    col1, col2,col4 = st.columns(3)
    
    with col1:
        st.metric("Total Regions", len(regional_features))
    
    with col2:
        n_clusters = len(regional_features['Cluster'].unique())
        st.metric("Number of Clusters", n_clusters)
    
    with col4:
        largest_cluster_size = regional_features['Cluster'].value_counts().max()
        st.metric("Largest Cluster", f"{largest_cluster_size} regions")

def cluster_visualization(regional_features, X_scaled, feature_cols):
    col1, col2 = st.columns(2)
    
    with col1:
        if len(X_scaled) > 1:
            pca = PCA(n_components=2)
            X_pca = pca.fit_transform(X_scaled)
            
            pca_df = pd.DataFrame({
                'PC1': X_pca[:, 0],
                'PC2': X_pca[:, 1],
                'Region': regional_features['REGIONAL_OFFICE_NAME'],
                'Cluster': regional_features['Cluster'],
                'Total_Cost': regional_features['Total_Cost']
            })
            
            fig_pca = px.scatter(
                pca_df,
                x='PC1',
                y='PC2',
                color='Cluster',
                size='Total_Cost',
                hover_name='Region',
                title="Regional Clusters",
                size_max=40
            )
            fig_pca.update_layout(height=400)
            st.plotly_chart(fig_pca, use_container_width=True)
    
    with col2:
        cluster_summary = regional_features.groupby('Cluster')[feature_cols].mean().round(2)
        
        display_summary = cluster_summary.copy()
        display_summary['Total_Cost'] = display_summary['Total_Cost'].apply(lambda x: f"£{x:,.0f}")
        display_summary['Mean_Cost'] = display_summary['Mean_Cost'].apply(lambda x: f"£{x:,.0f}")
        display_summary['Cost_Per_Record'] = display_summary['Cost_Per_Record'].apply(lambda x: f"£{x:,.0f}")
        display_summary.columns = ['Total Cost', 'Mean Cost', 'Cost Variability', 'Cost per Record']
        
        st.dataframe(display_summary, use_container_width=True)

def geographic_distribution(regional_features):
    map_data = []
    for _, row in regional_features.iterrows():
        region = row['REGIONAL_OFFICE_NAME']
        if region in REGION_COORDINATES:
            coords = REGION_COORDINATES[region]
            map_data.append({
                'Region': region,
                'Latitude': coords['lat'],
                'Longitude': coords['lon'],
                'Cluster': f"Cluster {row['Cluster']}",
                'Total_Cost': row['Total_Cost'],
                'Mean_Cost': row['Mean_Cost']
            })
    
    if map_data:
        map_df = pd.DataFrame(map_data)
        
        fig_map = px.scatter_mapbox(
            map_df,
            lat="Latitude",
            lon="Longitude",
            color="Cluster",
            size="Total_Cost",
            hover_name="Region",
            size_max=50,
            zoom=5.5,
            center={"lat": 54.0, "lon": -2.0},
            mapbox_style="open-street-map",
            title="Geographic Distribution"
        )
        
        fig_map.update_layout(height=500, margin={"r": 0, "t": 50, "l": 0, "b": 0})
        st.plotly_chart(fig_map, use_container_width=True)

def cluster_details(regional_features, feature_cols):
    for cluster_id in sorted(regional_features['Cluster'].unique()):
        cluster_data = regional_features[regional_features['Cluster'] == cluster_id]
        cluster_regions = cluster_data['REGIONAL_OFFICE_NAME'].tolist()
        cluster_stats = cluster_data[feature_cols].mean()
        
        with st.expander(f"Cluster {cluster_id} ({len(cluster_data)} regions)"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                for region in cluster_regions:
                    st.write(f"• {region}")
            
            with col2:
                st.write(f"**Total Cost**: £{cluster_stats['Total_Cost']:,.0f}")
                st.write(f"**Mean Cost**: £{cluster_stats['Mean_Cost']:,.0f}")
                st.write(f"**Cost Variability**: {cluster_stats['Cost_Variability']:.2f}")
                st.write(f"**Cost per Record**: £{cluster_stats['Cost_Per_Record']:,.0f}")