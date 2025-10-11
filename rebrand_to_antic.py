#!/usr/bin/env python3
"""
Script to rebrand from "Antici" to "'antic"
Updates all templates, database references, and documentation.
"""

import os
import re
import psycopg2
from pathlib import Path

def update_file_content(file_path, replacements):
    """Update file content with the given replacements"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Updated: {file_path}")
            return True
        else:
            print(f"⏭️  No changes needed: {file_path}")
            return False
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def main():
    print("🔄 Rebranding from 'Antici' to \"'antic\"")
    print("=" * 50)
    
    # Define all replacements
    replacements = {
        "Antici": "'antic",
        "antici_db": "antic_db"
    }
    
    # Get the current directory (should be /Users/stephencoan/antici)
    base_dir = Path.cwd()
    print(f"Working directory: {base_dir}")
    
    # Files to update
    files_to_update = [
        # Template files
        "templates/artists.html",
        "templates/artist_detail.html", 
        "templates/portfolio.html",
        "templates/add_artist.html",
        "templates/search_users.html",
        "templates/pending_requests.html",
        "templates/followers.html",
        "templates/following.html",
        "templates/settings.html",
        "templates/login.html",
        "templates/register.html",
        "templates/user_portfolio.html",
        "templates/base.html",
        "templates/portfolio_new.html",
        "templates/all_users.html",
        # Main application file
        "app.py",
        # Documentation
        "README.md"
    ]
    
    updated_files = 0
    
    # Update each file
    for file_path in files_to_update:
        full_path = base_dir / file_path
        if full_path.exists():
            if update_file_content(full_path, replacements):
                updated_files += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n📊 Summary: Updated {updated_files} files")
    
    # Database update instructions
    print("\n" + "=" * 50)
    print("🗄️  DATABASE UPDATE REQUIRED:")
    print("The database name reference has been updated in app.py")
    print("You have two options:")
    print("\n1. RENAME existing database:")
    print("   psql -U stephencoan")
    print("   ALTER DATABASE antici_db RENAME TO antic_db;")
    print("\n2. CREATE new database and migrate data:")
    print("   createdb -U stephencoan antic_db")
    print("   pg_dump antici_db | psql antic_db")
    print("\n⚠️  Don't forget to restart your Flask app after database changes!")
    
    print("\n🎉 Rebranding complete!")
    print("Files updated from 'Antici' to \"'antic\"")

if __name__ == "__main__":
    main()
