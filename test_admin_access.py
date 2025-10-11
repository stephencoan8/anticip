#!/usr/bin/env python3
"""
Test script to verify admin access controls are working properly.
"""

import requests
import sys

BASE_URL = "http://localhost:5004"

def test_admin_access():
    """Test admin access controls"""
    print("🧪 Testing Admin Access Controls")
    print("=" * 50)
    
    # Create a session for admin user
    admin_session = requests.Session()
    
    # Test 1: Login as admin user
    print("\n1. Testing admin login...")
    login_data = {
        'username': 'stephen',
        'password': 'password'  # Assuming this is the password
    }
    
    response = admin_session.post(f"{BASE_URL}/login", data=login_data)
    if response.status_code == 200 and "Artists" in response.text:
        print("   ✅ Admin login successful")
    else:
        print("   ❌ Admin login failed")
        print(f"   Status: {response.status_code}")
        return
    
    # Test 2: Check if admin badge is visible in sidebar
    print("\n2. Testing admin badge visibility...")
    response = admin_session.get(f"{BASE_URL}/artists")
    if "Admin" in response.text and "bg-yellow-100" in response.text:
        print("   ✅ Admin badge visible in sidebar")
    else:
        print("   ❌ Admin badge not found in sidebar")
    
    # Test 3: Check artist page for delete button
    print("\n3. Testing delete button visibility for admin...")
    # Use the first artist from our list
    artist_id = "0Cj5PLNNGVOsXUig1ic4s5"  # Noah Guy
    response = admin_session.get(f"{BASE_URL}/artist/{artist_id}")
    if response.status_code == 200 and "Delete Artist" in response.text:
        print("   ✅ Delete button visible for admin user")
    else:
        print("   ❌ Delete button not found for admin user")
    
    # Test 4: Test non-admin user
    print("\n4. Testing non-admin user access...")
    regular_session = requests.Session()
    
    login_data = {
        'username': 'scoan',
        'password': 'password'  # Assuming this is the password
    }
    
    response = regular_session.post(f"{BASE_URL}/login", data=login_data)
    if response.status_code == 200:
        print("   ✅ Regular user login successful")
        
        # Check no admin badge
        response = regular_session.get(f"{BASE_URL}/artists")
        if "Admin" not in response.text or "bg-yellow-100" not in response.text:
            print("   ✅ No admin badge for regular user")
        else:
            print("   ❌ Admin badge incorrectly shown for regular user")
        
        # Check no delete button
        response = regular_session.get(f"{BASE_URL}/artist/{artist_id}")
        if response.status_code == 200 and "Delete Artist" not in response.text:
            print("   ✅ Delete button hidden from regular user")
        else:
            print("   ❌ Delete button incorrectly shown to regular user")
        
        # Test direct access to delete route (should be blocked)
        response = regular_session.post(f"{BASE_URL}/delete_artist/{artist_id}")
        if response.status_code == 403 or "Admin access required" in response.text:
            print("   ✅ Direct delete access properly blocked for regular user")
        else:
            print("   ❌ Delete route not properly secured")
            print(f"   Status: {response.status_code}")
    else:
        print("   ❌ Regular user login failed")
    
    print("\n" + "=" * 50)
    print("🏁 Admin access control testing complete!")

if __name__ == "__main__":
    test_admin_access()
