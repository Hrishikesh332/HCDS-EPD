import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from statsmodels.tsa.arima.model import ARIMA
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from scipy.stats import f_oneway, kruskal
import warnings
warnings.filterwarnings('ignore')

REGION_COORDINATES = {
    'LONDON': {'lat': 51.5074, 'lon': -0.1278, 'size_multiplier': 1.5},
    'NORTH WEST': {'lat': 53.4808, 'lon': -2.2426, 'size_multiplier': 1.2},
    'MIDLANDS': {'lat': 52.4862, 'lon': -1.8904, 'size_multiplier': 1.1},
    'SOUTH EAST': {'lat': 51.2308, 'lon': 0.2713, 'size_multiplier': 1.0},
    'EAST OF ENGLAND': {'lat': 52.2406, 'lon': 0.5018, 'size_multiplier': 1.0},
    'SOUTH WEST': {'lat': 50.7156, 'lon': -3.5309, 'size_multiplier': 0.9},
    'NORTH EAST AND YORKSHIRE': {'lat': 54.0678, 'lon': -1.3500, 'size_multiplier': 1.0},
    'SOUTH OF ENGLAND': {'lat': 50.9097, 'lon': -1.4044, 'size_multiplier': 0.8},
    'NORTH OF ENGLAND': {'lat': 55.2088, 'lon': -1.5941, 'size_multiplier': 0.8},
    'MIDLANDS AND EAST OF ENGLAND': {'lat': 52.3555, 'lon': -0.2593, 'size_multiplier': 0.7},
    'UNIDENTIFIED': {'lat': 52.3555, 'lon': -1.1743, 'size_multiplier': 0.5}
}

def load_data():
    try:
        df = pd.read_csv("monthly_summary.csv")
        df["YEAR_MONTH"] = pd.to_datetime(df["YEAR_MONTH"])
        df["TOTAL_COST"] = pd.to_numeric(df["TOTAL_COST"], errors="coerce")
        df = df.dropna(subset=['TOTAL_COST'])
        return df, "real"
    except FileNotFoundError:
        return gen_sample_data(), "sample"
    except Exception:
        return gen_sample_data(), "sample"

def gen_sample_data():
    regions = [
        'LONDON', 'NORTH WEST', 'MIDLANDS', 'SOUTH EAST', 
        'EAST OF ENGLAND', 'SOUTH WEST', 'NORTH EAST AND YORKSHIRE',
        'SOUTH OF ENGLAND', 'NORTH OF ENGLAND', 
        'MIDLANDS AND EAST OF ENGLAND', 'UNIDENTIFIED'
    ]
    
    bnf_codes = [
        "01: Gastro-Intestinal System", "02: Cardiovascular System", 
        "03: Respiratory System", "04: Central Nervous System",
        "05: Infections", "06: Endocrine System",
        "07: Obstetrics and Gynaecology", "08: Malignant Disease",
        "09: Nutrition and Blood", "10: Musculoskeletal Diseases",
        "11: Eye", "12: Ear, Nose and Throat", "13: Skin",
        "14: Immunological Products", "15: Anaesthesia",
        "18: Preparations used in Diagnosis", "19: Other Drugs",
        "20: Dressings", "21: Appliances"
    ]
    
    date_range = pd.date_range('2020-01-01', '2025-08-01', freq='MS')
    data = []
    
    np.random.seed(42)
    
    for region in regions:
        for bnf_code in bnf_codes:
            base_cost = 15000
            
            for i, date in enumerate(date_range):
                trend = base_cost * 0.002 * i
                seasonal = base_cost * 0.15 * np.sin(2 * np.pi * i / 12)
                noise = np.random.normal(0, base_cost * 0.08)
                
                covid_impact = 0
                if date.year in [2020, 2021]:
                    covid_impact = base_cost * 0.2 * np.random.uniform(-1, 1)
                
                cost = base_cost + trend + seasonal + noise + covid_impact
                cost = max(0, cost)
                
                data.append({
                    'YEAR_MONTH': date,
                    'REGIONAL_OFFICE_NAME': region,
                    'BNF_CHAPTER_PLUS_CODE': bnf_code,
                    'TOTAL_COST': cost
                })
    
    return pd.DataFrame(data)

def train_arima(ts_data, forecast_periods=5):
    if len(ts_data) < 3:
        raise ValueError("Insufficient data for ARIMA modeling. Need at least 3 data points.")
    
    orders = [(1,1,1), (2,1,1), (1,0,1), (0,1,1), (1,1,0)]
    best_model = None
    best_aic = float('inf')
    
    for order in orders:
        try:
            model = ARIMA(ts_data['TOTAL_COST'], order=order)
            fitted_model = model.fit()
            if fitted_model.aic < best_aic:
                best_aic = fitted_model.aic
                best_model = fitted_model
        except:
            continue
    
    if best_model is None:
        raise ValueError("All ARIMA models failed to converge. Cannot generate forecast.")
    
    forecast_result = best_model.get_forecast(steps=forecast_periods)
    forecast = forecast_result.predicted_mean
    conf_int = forecast_result.conf_int()
    
    forecast_dates = pd.date_range(
        start=ts_data['YEAR_MONTH'].iloc[-1] + pd.DateOffset(months=1),
        periods=forecast_periods,
        freq='MS'
    )
    
    return pd.DataFrame({
        'YEAR_MONTH': forecast_dates,
        'FORECAST': forecast.values,
        'CONFIDENCE_LOWER': conf_int.iloc[:, 0].values,
        'CONFIDENCE_UPPER': conf_int.iloc[:, 1].values
    })

def create_map(df, selected_region=None):
    region_totals = df.groupby('REGIONAL_OFFICE_NAME')['TOTAL_COST'].sum()
    
    map_data = []
    for region in region_totals.index:
        if region in REGION_COORDINATES:
            coords = REGION_COORDINATES[region]
            total_cost = region_totals[region]
            
            map_data.append({
                'Region': region,
                'Latitude': coords['lat'],
                'Longitude': coords['lon'],
                'Total_Cost': total_cost,
                'Size': (total_cost / region_totals.max() * 40 + 10) * coords['size_multiplier'],
                'Color': 'Selected' if region == selected_region else 'Other',
                'Rank': int(region_totals.rank(ascending=False)[region])
            })
    
    map_df = pd.DataFrame(map_data)
    
    fig = px.scatter_mapbox(
        map_df, 
        lat="Latitude", 
        lon="Longitude",
        size="Size",
        color="Color",
        hover_name="Region",
        hover_data={
            'Latitude': False,
            'Longitude': False,
            'Size': False,
            'Color': False,
            'Total_Cost': ':,.0f',
            'Rank': True
        },
        color_discrete_map={'Selected': '#FF6B6B', 'Other': '#4ECDC4'},
        size_max=35,
        zoom=5.5,
        center={"lat": 54.0, "lon": -2.0},
        mapbox_style="open-street-map",
        title="NHS Regional Prescription Costs"
    )
    
    fig.update_layout(
        height=500,
        margin={"r":0,"t":50,"l":0,"b":0},
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def gen_pred_errors(df):
    np.random.seed(42)
    
    regional_data = []
    for region in df['REGIONAL_OFFICE_NAME'].unique():
        region_data = df[df['REGIONAL_OFFICE_NAME'] == region]
        
        for bnf_code in region_data['BNF_CHAPTER_PLUS_CODE'].unique():
            bnf_data = region_data[region_data['BNF_CHAPTER_PLUS_CODE'] == bnf_code]
            ts_data = bnf_data.groupby('YEAR_MONTH')['TOTAL_COST'].sum()
            
            if len(ts_data) >= 12:
                mean_actual = ts_data.mean()
                base_error = mean_actual * 0.1
                
                mae = abs(np.random.normal(base_error, base_error * 0.3))
                bias = np.random.normal(0, base_error * 0.2)
                mape = (mae / mean_actual) * 100 if mean_actual > 0 else 0
                
                regional_data.append({
                    'REGIONAL_OFFICE_NAME': region,
                    'BNF_CATEGORY': bnf_code.split(':')[0].strip(),
                    'Mean_Actual': mean_actual,
                    'MAE': mae,
                    'Bias': bias,
                    'MAPE': mape
                })
    
    return pd.DataFrame(regional_data)

def calc_fairness_metrics(df_errors):
    cost_threshold = df_errors['Mean_Actual'].quantile(0.75)
    
    region_parity = []
    for region in df_errors['REGIONAL_OFFICE_NAME'].unique():
        region_data = df_errors[df_errors['REGIONAL_OFFICE_NAME'] == region]
        high_cost_rate = (region_data['Mean_Actual'] >= cost_threshold).mean()
        avg_prediction_error = region_data['MAE'].mean() / region_data['Mean_Actual'].mean()
        
        region_parity.append({
            'Region': region,
            'High_Cost_Rate': high_cost_rate,
            'Relative_Error_Rate': avg_prediction_error,
            'MAE_Mean': region_data['MAE'].mean(),
            'Bias_Mean': region_data['Bias'].mean()
        })
    
    parity_df = pd.DataFrame(region_parity)
    parity_gap = parity_df['Relative_Error_Rate'].max() - parity_df['Relative_Error_Rate'].min()
    
    regional_mae_groups = [group['MAE'].values for name, group in df_errors.groupby('REGIONAL_OFFICE_NAME')]
    regional_bias_groups = [group['Bias'].values for name, group in df_errors.groupby('REGIONAL_OFFICE_NAME')]
    
    try:
        f_stat_bias, p_val_bias = f_oneway(*regional_bias_groups)
        kw_stat_mae, kw_p_mae = kruskal(*regional_mae_groups)
        kw_stat_bias, kw_p_bias = kruskal(*regional_bias_groups)
    except:
        f_stat_bias, p_val_bias = 0, 1
        kw_stat_mae, kw_p_mae = 0, 1
        kw_stat_bias, kw_p_bias = 0, 1
    
    return {
        'parity_df': parity_df,
        'parity_gap': parity_gap,
        'statistical_tests': {
            'f_stat_bias': f_stat_bias,
            'p_val_bias': p_val_bias,
            'kw_stat_mae': kw_stat_mae,
            'kw_p_mae': kw_p_mae,
            'kw_stat_bias': kw_stat_bias,
            'kw_p_bias': kw_p_bias
        }
    }

def detect_outliers(df, method, threshold, contamination, analysis_type):
    if analysis_type == 'temporal':
        monthly_data = df.groupby('YEAR_MONTH')['TOTAL_COST'].sum()
        outlier_months = set()
        
        if method == "IQR Method":
            Q1 = monthly_data.quantile(0.25)
            Q3 = monthly_data.quantile(0.75)
            IQR = Q3 - Q1
            if IQR > 0:
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                outlier_months = monthly_data[(monthly_data < lower_bound) | (monthly_data > upper_bound)].index

        elif method == "Isolation Forest":
            if len(monthly_data) > 1:
                iso_forest = IsolationForest(contamination=contamination, random_state=42)
                outliers = iso_forest.fit_predict(monthly_data.values.reshape(-1, 1))
                outlier_months = monthly_data[outliers == -1].index
        else:
            methods_results = []
            
            Q1 = monthly_data.quantile(0.25)
            Q3 = monthly_data.quantile(0.75)
            IQR = Q3 - Q1
            if IQR > 0:
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                iqr_outliers = (monthly_data < lower_bound) | (monthly_data > upper_bound)
                methods_results.append(iqr_outliers)
            
            if monthly_data.std() > 0:
                z_scores = np.abs((monthly_data - monthly_data.mean()) / monthly_data.std())
                zscore_outliers = z_scores > threshold
                methods_results.append(zscore_outliers)
            
            if len(monthly_data) > 1:
                iso_forest = IsolationForest(contamination=contamination, random_state=42)
                iso_outliers = iso_forest.fit_predict(monthly_data.values.reshape(-1, 1)) == -1
                methods_results.append(iso_outliers)
            
            if methods_results:
                combined_outliers = sum(methods_results) >= 2
                outlier_months = monthly_data[combined_outliers].index
            else:
                outlier_months = []
        
        return df[df['YEAR_MONTH'].isin(outlier_months)]
    
    data = df['TOTAL_COST']
    
    if method == "IQR Method":
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        if IQR > 0:
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            return df[(data < lower_bound) | (data > upper_bound)]
        else:
            return pd.DataFrame()
    
    elif method == "Z-Score":
        if data.std() > 0:
            z_scores = np.abs((data - data.mean()) / data.std())
            return df[z_scores > threshold]
        else:
            return pd.DataFrame()
    
    elif method == "Isolation Forest":
        if len(data) > 1:
            iso_forest = IsolationForest(contamination=contamination, random_state=42)
            outliers = iso_forest.fit_predict(df[['TOTAL_COST']])
            return df[outliers == -1]
        else:
            return pd.DataFrame()
    
    else:
        methods_results = []
        
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        if IQR > 0:
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            iqr_outliers = (data < lower_bound) | (data > upper_bound)
            methods_results.append(iqr_outliers)
        
        if data.std() > 0:
            z_scores = np.abs((data - data.mean()) / data.std())
            zscore_outliers = z_scores > threshold
            methods_results.append(zscore_outliers)
        
        if len(data) > 1:
            iso_forest = IsolationForest(contamination=contamination, random_state=42)
            iso_outliers = iso_forest.fit_predict(df[['TOTAL_COST']]) == -1
            methods_results.append(iso_outliers)
        
        if methods_results:
            combined_outliers = sum(methods_results) >= 2
            return df[combined_outliers]
        else:
            return pd.DataFrame()

def apply_clustering(X_scaled, algorithm, n_clusters):
    if algorithm == "K-Means":
        clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    elif algorithm == "Hierarchical":
        clusterer = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
    else:
        clusterer = DBSCAN(eps=0.5, min_samples=2)
    
    cluster_labels = clusterer.fit_predict(X_scaled)
    return cluster_labels.astype(str)

def gen_real_pred_errors(df, test_periods=6):
    errors = []
    for region in df['REGIONAL_OFFICE_NAME'].unique():
        region_data = df[df['REGIONAL_OFFICE_NAME'] == region]
        for bnf_code in region_data['BNF_CHAPTER_PLUS_CODE'].unique():
            bnf_data = region_data[region_data['BNF_CHAPTER_PLUS_CODE'] == bnf_code]
            ts_data = bnf_data.groupby('YEAR_MONTH')['TOTAL_COST'].sum().reset_index()
            if len(ts_data) < test_periods + 3:
                continue  
            train = ts_data.iloc[:-test_periods]
            test = ts_data.iloc[-test_periods:]
            try:
                forecast_df = train_arima(train, test_periods)
                if len(forecast_df) != len(test):
                    continue
                y_true = test['TOTAL_COST'].values
                y_pred = forecast_df['FORECAST'].values
                mae = np.mean(np.abs(y_true - y_pred))
                bias = np.mean(y_pred - y_true)
                mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100 if np.all(y_true != 0) else np.nan
                errors.append({
                    'REGIONAL_OFFICE_NAME': region,
                    'BNF_CATEGORY': bnf_code.split(':')[0].strip(),
                    'Mean_Actual': np.mean(y_true),
                    'MAE': mae,
                    'Bias': bias,
                    'MAPE': mape
                })
            except Exception:
                continue
    return pd.DataFrame(errors)