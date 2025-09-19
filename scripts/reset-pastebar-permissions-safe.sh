#!/bin/bash

# PasteBar - Safe Accessibility Permissions Reset Script
# This script ONLY affects PasteBar, not other applications

echo "🔧 PasteBar Safe Accessibility Permissions Reset"
echo "==============================================="
echo ""
echo "⚠️  This script will ONLY remove PasteBar's accessibility permissions."
echo "    Other applications will NOT be affected."
echo ""

# Get the bundle identifier
BUNDLE_ID="app.anothervision.pasteBar"
echo "📱 Target Bundle ID: $BUNDLE_ID"
echo ""

# Check if PasteBar is running
if pgrep -f "PasteBar" > /dev/null; then
    echo "⚠️  PasteBar is currently running."
    echo "   Please quit PasteBar before continuing."
    echo ""
    echo "   Ways to quit PasteBar:"
    echo "   • Right-click the PasteBar icon in the menu bar and select 'Quit'"
    echo "   • Use Activity Monitor to force quit"
    echo "   • Press Cmd+Q while PasteBar window is active"
    echo ""
    read -p "Press Enter after quitting PasteBar to continue..."
    echo ""
fi

# Function to check if TCC database exists and is accessible
check_tcc_db() {
    local db_path="$1"
    local db_type="$2"
    
    if [ ! -f "$db_path" ]; then
        echo "   ❌ $db_type TCC database not found: $db_path"
        return 1
    fi
    
    # Try to query the database
    if ! sqlite3 "$db_path" "SELECT COUNT(*) FROM access WHERE client='$BUNDLE_ID';" >/dev/null 2>&1; then
        echo "   ❌ Cannot access $db_type TCC database (permission denied or corrupted)"
        return 1
    fi
    
    return 0
}

# Function to show current permissions
show_current_permissions() {
    echo "🔍 Checking current PasteBar permissions..."
    
    # Check system TCC database
    if check_tcc_db "/Library/Application Support/com.apple.TCC/TCC.db" "System"; then
        local system_count=$(sudo sqlite3 "/Library/Application Support/com.apple.TCC/TCC.db" "SELECT COUNT(*) FROM access WHERE client='$BUNDLE_ID';" 2>/dev/null || echo "0")
        echo "   📊 System-level permissions: $system_count entries"
        
        if [ "$system_count" -gt 0 ]; then
            echo "   📋 System permissions details:"
            sudo sqlite3 "/Library/Application Support/com.apple.TCC/TCC.db" "SELECT '      ' || service || ': ' || CASE auth_value WHEN 0 THEN 'Denied' WHEN 1 THEN 'Unknown' WHEN 2 THEN 'Allowed' ELSE 'Other' END FROM access WHERE client='$BUNDLE_ID';" 2>/dev/null || echo "      Unable to read details"
        fi
    fi
    
    # Check user TCC database
    local user_tcc_path="$HOME/Library/Application Support/com.apple.TCC/TCC.db"
    if check_tcc_db "$user_tcc_path" "User"; then
        local user_count=$(sqlite3 "$user_tcc_path" "SELECT COUNT(*) FROM access WHERE client='$BUNDLE_ID';" 2>/dev/null || echo "0")
        echo "   📊 User-level permissions: $user_count entries"
        
        if [ "$user_count" -gt 0 ]; then
            echo "   📋 User permissions details:"
            sqlite3 "$user_tcc_path" "SELECT '      ' || service || ': ' || CASE auth_value WHEN 0 THEN 'Denied' WHEN 1 THEN 'Unknown' WHEN 2 THEN 'Allowed' ELSE 'Other' END FROM access WHERE client='$BUNDLE_ID';" 2>/dev/null || echo "      Unable to read details"
        fi
    fi
    echo ""
}

# Function to remove permissions
remove_permissions() {
    echo "🗑️  Removing PasteBar accessibility permissions..."
    
    local removed_any=false
    
    # Remove from system TCC database
    if check_tcc_db "/Library/Application Support/com.apple.TCC/TCC.db" "System"; then
        echo "   🔧 Removing from system TCC database..."
        if sudo sqlite3 "/Library/Application Support/com.apple.TCC/TCC.db" "DELETE FROM access WHERE client='$BUNDLE_ID';" 2>/dev/null; then
            echo "   ✅ System permissions removed"
            removed_any=true
        else
            echo "   ❌ Failed to remove system permissions"
        fi
    fi
    
    # Remove from user TCC database
    local user_tcc_path="$HOME/Library/Application Support/com.apple.TCC/TCC.db"
    if check_tcc_db "$user_tcc_path" "User"; then
        echo "   🔧 Removing from user TCC database..."
        if sqlite3 "$user_tcc_path" "DELETE FROM access WHERE client='$BUNDLE_ID';" 2>/dev/null; then
            echo "   ✅ User permissions removed"
            removed_any=true
        else
            echo "   ❌ Failed to remove user permissions"
        fi
    fi
    
    if [ "$removed_any" = true ]; then
        echo ""
        echo "✅ PasteBar permissions successfully removed!"
        echo "   Other applications are unaffected."
    else
        echo ""
        echo "ℹ️  No PasteBar permissions found to remove."
    fi
}

# Main execution
show_current_permissions

echo "❓ Do you want to remove PasteBar's accessibility permissions?"
echo "   This will require PasteBar to request permissions again on next launch."
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    remove_permissions
    
    echo ""
    echo "📋 Next steps:"
    echo "   1. Launch PasteBar"
    echo "   2. When the permission dialog appears, click 'Grant Permission'"
    echo "   3. Follow the system prompts to add PasteBar to Accessibility"
    echo ""
    echo "💡 If issues persist:"
    echo "   • Restart your Mac"
    echo "   • Check System Settings > Privacy & Security > Accessibility"
    echo "   • Ensure PasteBar is in the list and enabled"
else
    echo "❌ Operation cancelled. No changes made."
fi

echo ""
echo "🏁 Script completed."
