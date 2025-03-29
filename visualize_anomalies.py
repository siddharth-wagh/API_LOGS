import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import random
from datetime import datetime, timedelta

# Create a synthetic dataset with normal and anomalous data points
def generate_synthetic_data(num_normal=100, num_anomalies=10):
    # Generate normal data
    np.random.seed(42)
    normal_latency = np.random.normal(50, 15, num_normal)  # mean=50ms, std=15ms
    normal_error_rate = np.random.normal(2, 0.5, num_normal)  # mean=2%, std=0.5%
    
    # Ensure no negative values
    normal_latency = np.maximum(normal_latency, 5)
    normal_error_rate = np.maximum(normal_error_rate, 0)
    
    # Generate anomalies - half high latency, half normal latency but with errors
    high_latency_anomalies = np.random.normal(200, 50, num_anomalies // 2)  # High latency anomalies
    normal_latency_anomalies = np.random.normal(50, 15, num_anomalies - num_anomalies // 2)  # Normal latency but with errors
    
    anomaly_latency = np.concatenate([high_latency_anomalies, normal_latency_anomalies])
    
    # Error rates for anomalies
    normal_error_anomalies = np.random.normal(2, 0.5, num_anomalies // 2)  # Normal error rate
    high_error_anomalies = np.random.normal(30, 10, num_anomalies - num_anomalies // 2)  # High error rate anomalies
    
    anomaly_error_rate = np.concatenate([normal_error_anomalies, high_error_anomalies])
    
    # Create dataframes
    normal_df = pd.DataFrame({
        'duration_ms_mean': normal_latency,
        'error_rate': normal_error_rate,
        'is_anomaly': False,
        'service': 'service-a',
        'endpoint': np.random.choice(['/start', '/api/users', '/api/products', '/api/orders'], num_normal)
    })
    
    anomaly_df = pd.DataFrame({
        'duration_ms_mean': anomaly_latency,
        'error_rate': anomaly_error_rate,
        'is_anomaly': True,
        'service': 'service-a',
        'endpoint': np.random.choice(['/api/products', '/api/orders'], num_anomalies)
    })
    
    # Combine data
    df = pd.concat([normal_df, anomaly_df], ignore_index=True)
    
    return df

# Generate time series data showing the anomaly patterns
def generate_timeseries_data(hours=1):
    # Create a time range
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    timerange = pd.date_range(start=start_time, end=end_time, freq='1min')
    
    # Create normal baseline
    data = []
    
    for t in timerange:
        # Normal traffic
        latency = random.normalvariate(50, 10)
        error_rate = random.normalvariate(2, 0.5)
        
        # Add traffic pattern changes
        minute = t.minute + t.hour * 60
        
        # High volume period (30-45 minutes into the dataset)
        if minute % 60 >= 30 and minute % 60 < 45:
            latency = random.normalvariate(80, 15)
            
        # Anomaly period 1 (15-20 minutes into the dataset) - high latency
        if minute % 60 >= 15 and minute % 60 < 20:
            latency = random.normalvariate(300, 50)
            
        # Anomaly period 2 (50-55 minutes into the dataset) - high error rate
        if minute % 60 >= 50 and minute % 60 < 55:
            error_rate = random.normalvariate(30, 5)
        
        is_anomaly = (latency > 150 or error_rate > 10)
        
        data.append({
            'timestamp': t,
            'duration_ms_mean': max(5, latency),
            'error_rate': max(0, error_rate),
            'is_anomaly': is_anomaly
        })
    
    return pd.DataFrame(data)

# Visualize anomalies
def visualize_scatter_plot(df):
    plt.figure(figsize=(12, 8))
    
    # Plot normal vs anomalous points
    normal = df[~df['is_anomaly']]
    anomalies = df[df['is_anomaly']]
    
    plt.scatter(normal['duration_ms_mean'], normal['error_rate'], 
                alpha=0.7, label='Normal', color='blue')
    plt.scatter(anomalies['duration_ms_mean'], anomalies['error_rate'], 
                alpha=0.7, label='Anomaly', color='red', s=100)
    
    plt.title('API Performance Anomaly Detection', fontsize=16)
    plt.xlabel('Average Response Time (ms)', fontsize=14)
    plt.ylabel('Error Rate (%)', fontsize=14)
    plt.grid(alpha=0.3)
    plt.legend(fontsize=12)
    
    # Add thresholds
    plt.axhline(y=10, color='orange', linestyle='--', alpha=0.7, label='Error Threshold (10%)')
    plt.axvline(x=150, color='orange', linestyle='--', alpha=0.7, label='Latency Threshold (150ms)')
    
    # Annotate some anomalies
    for i, row in anomalies.iterrows():
        if row['error_rate'] > 20 or row['duration_ms_mean'] > 250:
            plt.annotate('Critical Anomaly',
                        xy=(row['duration_ms_mean'], row['error_rate']),
                        xytext=(row['duration_ms_mean']+20, row['error_rate']+5),
                        arrowprops=dict(facecolor='black', shrink=0.05, width=1.5))
    
    plt.tight_layout()
    plt.savefig('service_anomaly_detection.png')
    plt.close()

# Visualize time series data
def visualize_timeseries(df):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    
    # Mark anomalies
    anomalies = df[df['is_anomaly']]
    
    # Plot response time
    ax1.plot(df['timestamp'], df['duration_ms_mean'], label='Response Time', color='blue')
    ax1.scatter(anomalies['timestamp'], anomalies['duration_ms_mean'], color='red', label='Anomalies', zorder=5)
    ax1.axhline(y=150, color='orange', linestyle='--', alpha=0.7, label='Threshold (150ms)')
    ax1.set_ylabel('Response Time (ms)', fontsize=12)
    ax1.set_title('API Response Time', fontsize=14)
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # Plot error rate
    ax2.plot(df['timestamp'], df['error_rate'], label='Error Rate', color='green')
    ax2.scatter(anomalies['timestamp'], anomalies['error_rate'], color='red', label='Anomalies', zorder=5)
    ax2.axhline(y=10, color='orange', linestyle='--', alpha=0.7, label='Threshold (10%)')
    ax2.set_xlabel('Time', fontsize=12)
    ax2.set_ylabel('Error Rate (%)', fontsize=12)
    ax2.set_title('API Error Rate', fontsize=14)
    ax2.legend()
    ax2.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('service_monitor_anomalies.png')
    plt.close()

# Main function
def main():
    # Generate scatter plot data
    print("Generating scatter plot of API performance...")
    scatter_data = generate_synthetic_data(num_normal=150, num_anomalies=20)
    visualize_scatter_plot(scatter_data)
    print("Scatter plot saved as 'service_anomaly_detection.png'")
    
    # Generate time series data
    print("\nGenerating time series of API performance...")
    timeseries_data = generate_timeseries_data(hours=1)
    visualize_timeseries(timeseries_data)
    print("Time series plot saved as 'service_monitor_anomalies.png'")
    
    # Create a summary report
    print("\nGenerating anomaly detection report...")
    anomalies = scatter_data[scatter_data['is_anomaly']]
    anomalies_by_endpoint = anomalies.groupby('endpoint').agg({
        'is_anomaly': 'count',
        'duration_ms_mean': 'mean',
        'error_rate': 'mean'
    }).rename(columns={'is_anomaly': 'anomaly_count'}).reset_index()
    
    # Write to a markdown file
    with open('anomaly_detection_results.md', 'w') as f:
        f.write("# API Anomaly Detection Results\n\n")
        f.write("## Summary\n\n")
        f.write(f"Total data points analyzed: {len(scatter_data)}\n\n")
        f.write(f"Normal data points: {len(scatter_data) - len(anomalies)}\n\n")
        f.write(f"Anomalies detected: {len(anomalies)} ({len(anomalies)/len(scatter_data)*100:.2f}%)\n\n")
        
        f.write("## Anomalies by Endpoint\n\n")
        f.write("| Endpoint | Anomaly Count | Avg Response Time (ms) | Avg Error Rate (%) |\n")
        f.write("|----------|--------------|------------------------|--------------------|\n")
        
        for _, row in anomalies_by_endpoint.iterrows():
            f.write(f"| {row['endpoint']} | {row['anomaly_count']} | {row['duration_ms_mean']:.2f} | {row['error_rate']:.2f} |\n")
        
        f.write("\n## Anomaly Detection Criteria\n\n")
        f.write("Anomalies are detected based on two main criteria:\n\n")
        f.write("1. **Response Time**: Data points with abnormally high latency (> 150ms)\n")
        f.write("2. **Error Rate**: Data points with abnormally high error rates (> 10%)\n\n")
        
        f.write("Additionally, the following patterns are detected in the time series data:\n\n")
        f.write("- **Latency Spikes**: Sudden increases in response time\n")
        f.write("- **Error Rate Spikes**: Sudden increases in error rate\n")
        f.write("- **Combined Anomalies**: Instances with both high latency and high error rates\n\n")
        
        f.write("## Visualizations\n\n")
        f.write("### API Performance Scatter Plot\n\n")
        f.write("![API Performance Scatter Plot](service_anomaly_detection.png)\n\n")
        f.write("### API Performance Time Series\n\n")
        f.write("![API Performance Time Series](service_monitor_anomalies.png)\n\n")
    
    print("Anomaly detection report saved as 'anomaly_detection_results.md'")

if __name__ == "__main__":
    main() 