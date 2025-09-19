#!/bin/bash

# PasteBar - Reset macOS Accessibility Permissions Script
# This script helps reset accessibility permissions for PasteBar

echo "🔧 PasteBar Accessibility Permissions Reset Tool"
echo "================================================"
echo ""

# Get the bundle identifier from tauri.conf.json
BUNDLE_ID="app.anothervision.pasteBar"
echo "📱 Bundle ID: $BUNDLE_ID"
echo ""

# Check if PasteBar is running
if pgrep -f "PasteBar" > /dev/null; then
    echo "⚠️  PasteBar is currently running. Please quit the application first."
    echo "   You can quit PasteBar from the menu bar or use Activity Monitor."
    echo ""
    read -p "Press Enter after quitting PasteBar to continue..."
fi

echo "🧹 Clearing PasteBar accessibility permissions..."

# First, let's check what permissions exist for PasteBar
echo "   Checking existing permissions for PasteBar..."
echo "   System TCC database:"
sudo sqlite3 /Library/Application\ Support/com.apple.TCC/TCC.db "SELECT service, client, auth_value, auth_reason FROM access WHERE client='$BUNDLE_ID';" 2>/dev/null || echo "   No system-level permissions found"

if [ -f ~/Library/Application\ Support/com.apple.TCC/TCC.db ]; then
    echo "   User TCC database:"
    sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db "SELECT service, client, auth_value, auth_reason FROM access WHERE client='$BUNDLE_ID';" 2>/dev/null || echo "   No user-level permissions found"
fi

echo ""
read -p "Do you want to proceed with removing PasteBar's accessibility permissions? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Reset TCC (Transparency, Consent, and Control) database for accessibility - ONLY for PasteBar
    echo "   Removing PasteBar from system TCC database..."
    sudo sqlite3 /Library/Application\ Support/com.apple.TCC/TCC.db "DELETE FROM access WHERE client='$BUNDLE_ID' AND service='kTCCServiceAccessibility';"

    # Also reset user-level TCC database - ONLY for PasteBar
    if [ -f ~/Library/Application\ Support/com.apple.TCC/TCC.db ]; then
        echo "   Removing PasteBar from user TCC database..."
        sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db "DELETE FROM access WHERE client='$BUNDLE_ID' AND service='kTCCServiceAccessibility';"
    fi

    # Note: We're NOT clearing the global accessibility cache to avoid affecting other apps
    echo "   ✅ PasteBar permissions removed (other apps unaffected)"
else
    echo "   ❌ Operation cancelled"
    exit 0
fi

echo ""
echo "✅ Accessibility permissions have been reset!"
echo ""
echo "📋 Next steps:"
echo "   1. Launch PasteBar"
echo "   2. When prompted, grant accessibility permissions"
echo "   3. The app should now work properly"
echo ""
echo "💡 If you still experience issues:"
echo "   - Go to System Settings > Privacy & Security > Accessibility"
echo "   - Remove PasteBar from the list if it appears"
echo "   - Restart PasteBar and grant permissions when prompted"
echo ""
