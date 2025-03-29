#!/usr/bin/env python3
"""
AI Anomaly Detector - Main Entry Point

This is the main entry point for the AI Anomaly Detector product.
It provides a unified interface to the different components.
"""

import os
import sys
import argparse
import time
from datetime import datetime

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_header():
    """Print the header for the AI Anomaly Detector product."""
    print("\n" + "=" * 60)
    print("  🔍 AI ANOMALY DETECTOR - MICROSERVICE MONITORING SYSTEM")
    print("=" * 60)
    print("  Detect anomalies in your microservices using machine learning")
    print("  Current time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60 + "\n")

def collect_data():
    """Run the data collection module."""
    print("📊 Starting data collection...")
    from data_collection.inject_service_data import process_and_inject_service_logs
    num_logs = process_and_inject_service_logs()
    print(f"✅ Data collection complete. Processed {num_logs} logs.")
    return num_logs

def train_model():
    """Run the model training module."""
    print("🧠 Starting model training...")
    # We need to temporarily change directory to work with relative imports
    current_dir = os.getcwd()
    os.chdir(os.path.join(current_dir, 'training'))
    sys.path.append(os.path.join(current_dir, 'training'))
    
    # Import and run the training module
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "train_model_from_services", 
            os.path.join(current_dir, "training", "train_model_from_services.py")
        )
        training_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(training_module)
        # Ideally we would call a function here, but since the script is designed
        # to run directly, we rely on its execution to perform the training
    except Exception as e:
        print(f"❌ Error during model training: {e}")
    finally:
        os.chdir(current_dir)
        
    print("✅ Model training complete.")

def start_monitoring():
    """Start the monitoring service."""
    print("👁️ Starting monitoring service...")
    
    # Import the monitor module
    try:
        from monitoring.monitor_services import ServiceMonitor
        monitor = ServiceMonitor(check_interval=30)
        monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n⏹️ Monitoring stopped by user.")
    except Exception as e:
        print(f"❌ Error during monitoring: {e}")
    
    print("✅ Monitoring complete.")

def generate_anomalies():
    """Generate artificial anomalies for testing."""
    print("⚠️ Generating artificial anomalies...")
    
    # Import and run the anomaly generator
    try:
        from testing.generate_anomalies import generate_mixed_anomaly_pattern
        generate_mixed_anomaly_pattern()
    except KeyboardInterrupt:
        print("\n⏹️ Anomaly generation stopped by user.")
    except Exception as e:
        print(f"❌ Error during anomaly generation: {e}")
    
    print("✅ Anomaly generation complete.")

def main():
    """Main entry point for the AI Anomaly Detector."""
    print_header()
    
    parser = argparse.ArgumentParser(description="AI Anomaly Detector - Microservice Monitoring System")
    parser.add_argument("--collect", action="store_true", help="Collect data from services")
    parser.add_argument("--train", action="store_true", help="Train the anomaly detection model")
    parser.add_argument("--monitor", action="store_true", help="Start the monitoring service")
    parser.add_argument("--generate", action="store_true", help="Generate artificial anomalies")
    parser.add_argument("--all", action="store_true", help="Run all steps in sequence")
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    # Run all steps in sequence
    if args.all:
        collect_data()
        train_model()
        # Start monitoring in the background
        import threading
        monitor_thread = threading.Thread(target=start_monitoring)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Generate anomalies
        generate_anomalies()
        
        # Wait for monitoring to detect anomalies
        print("\n🔍 Waiting for monitoring to detect anomalies...\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ AI Anomaly Detector stopped by user.")
        return
    
    # Run individual steps as requested
    if args.collect:
        collect_data()
    
    if args.train:
        train_model()
    
    if args.generate:
        generate_anomalies()
    
    if args.monitor:
        start_monitoring()

if __name__ == "__main__":
    main() 