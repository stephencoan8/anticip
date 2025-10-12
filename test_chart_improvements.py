#!/usr/bin/env python3
"""
Test script for chart improvements with time range filtering
"""

import requests
import json
from datetime import datetime, timedelta

# Base URL for the application
BASE_URL = "http://127.0.0.1:5004"

def test_chart_improvements():
    """Test the new chart improvements"""
    
    print("🧪 Testing Chart Improvements...")
    print("=" * 50)
    
    # Test session login
    session = requests.Session()
    
    # Login with test user
    login_data = {
        'username': 'stephen2',
        'password': 'test123'  # Assuming test password
    }
    
    print("1. Testing login...")
    login_response = session.post(f"{BASE_URL}/login", data=login_data)
    if login_response.status_code == 200 and 'portfolio' in login_response.url:
        print("   ✅ Login successful")
    else:
        print("   ❌ Login failed - trying without login for API structure test")
    
    # Test portfolio history API with different time ranges
    print("\n2. Testing portfolio history API endpoints...")
    time_ranges = ['1week', '1month', '3months', '1year', 'all']
    
    for range_param in time_ranges:
        try:
            response = session.get(f"{BASE_URL}/portfolio_history/1?range={range_param}")
            print(f"   📊 {range_param}: Status {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'datasets' in data and len(data['datasets']) > 0:
                    data_points = len(data['datasets'][0]['data'])
                    print(f"      📈 Data points: {data_points}")
                    
                    # Check if data is in proper time format
                    if data_points > 0:
                        sample_point = data['datasets'][0]['data'][0]
                        if isinstance(sample_point, dict) and 'x' in sample_point and 'y' in sample_point:
                            print(f"      ✅ Proper time format: {sample_point['x']}")
                        else:
                            print(f"      ⚠️  Data format: {sample_point}")
            else:
                print(f"      ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error testing {range_param}: {e}")
    
    # Test artist history API
    print("\n3. Testing artist history API endpoints...")
    
    # Get a test artist spotify_id from database
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            database="anticip_db",
            user="stephencoan",
            password=""
        )
        cursor = conn.cursor()
        cursor.execute("SELECT spotify_id, name FROM artists LIMIT 1")
        artist_row = cursor.fetchone()
        
        if artist_row:
            spotify_id, artist_name = artist_row
            print(f"   🎵 Testing with artist: {artist_name} ({spotify_id})")
            
            for range_param in time_ranges:
                try:
                    response = session.get(f"{BASE_URL}/api/artist_history/{spotify_id}?range={range_param}")
                    print(f"   📊 {range_param}: Status {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'datasets' in data and len(data['datasets']) > 0:
                            data_points = len(data['datasets'][0]['data'])
                            print(f"      📈 Data points: {data_points}")
                            
                            # Check data format
                            if data_points > 0:
                                sample_point = data['datasets'][0]['data'][0]
                                if isinstance(sample_point, dict) and 'x' in sample_point and 'y' in sample_point:
                                    print(f"      ✅ Proper time format: {sample_point['x']}")
                    else:
                        print(f"      ❌ Error: {response.text}")
                        
                except Exception as e:
                    print(f"   ❌ Error testing {range_param}: {e}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Database connection error: {e}")
    
    # Test page loads
    print("\n4. Testing page loads with new chart components...")
    
    pages_to_test = [
        ('/portfolio', 'Portfolio page'),
        ('/artists', 'Artists page'),
    ]
    
    for url, name in pages_to_test:
        try:
            response = session.get(f"{BASE_URL}{url}")
            print(f"   📄 {name}: Status {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                # Check for time range buttons
                if 'time-range-btn' in content:
                    print("      ✅ Time range buttons found")
                else:
                    print("      ⚠️  Time range buttons not found")
                
                # Check for Chart.js
                if 'chart.js' in content:
                    print("      ✅ Chart.js loaded")
                else:
                    print("      ⚠️  Chart.js not found")
                    
                # Check for date adapter
                if 'chartjs-adapter-date-fns' in content:
                    print("      ✅ Date adapter loaded")
                else:
                    print("      ⚠️  Date adapter not found")
            
        except Exception as e:
            print(f"   ❌ Error testing {name}: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Chart improvement tests completed!")
    print("✨ Features added:")
    print("   • Time range filtering (1W, 1M, 3M, 1Y, All)")
    print("   • Proper calendar date scaling")
    print("   • Interactive time range buttons")
    print("   • Chart.js time adapter integration")

if __name__ == "__main__":
    test_chart_improvements()
