#!/usr/bin/env python3
"""
Script to REVERT rebranding from "'antic" back to "Antici"
Undoes all the previous changes.
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
            print(f"✅ Reverted: {file_path}")
            return True
        else:
            print(f"⏭️  No changes needed: {file_path}")
            return False
    except Exception as e:
        print(f"❌ Error reverting {file_path}: {e}")
        return False

def main():
    print("🔄 REVERTING: Changing \"'antic\" back to 'Antici'")
    print("=" * 50)
    
    # Define all replacements (REVERSE of what we did before)
    replacements = {
        "'antic": "Antici",
        "antic_db": "antici_db"
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
    
    print(f"\n📊 Summary: Reverted {updated_files} files")
    
    print("\n🎉 REVERSION COMPLETE!")
    print("All files changed back from \"'antic\" to 'Antici'")

if __name__ == "__main__":
    main()
