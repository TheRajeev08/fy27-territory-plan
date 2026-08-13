#!/bin/bash
# One-step installer for the FY27 Territory Plan Copilot plugin.
#
# Non-technical teammates should never have to reason about clone paths or
# Python packaging, so this does the whole install and says plainly whether it
# worked. Safe to re-run: an existing install is updated, not duplicated.

set -u

REPO="https://github.com/TheRajeev08/fy27-territory-plan.git"
DEST="$HOME/.copilot/installed-plugins/fy27-territory-plan"

echo ""
echo "Installing the FY27 Territory Plan plugin..."
echo ""

if ! command -v git >/dev/null 2>&1; then
    echo "X  Git is not installed on this Mac."
    echo "   Open the App Store and install Xcode command line tools, or ask IT."
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "X  Python 3 is not installed on this Mac."
    echo "   Install it from https://www.python.org/downloads/ then run this again."
    exit 1
fi

fetch_plugin() {
    rm -rf "$DEST"
    mkdir -p "$(dirname "$DEST")"
    git clone --quiet "$REPO" "$DEST" 2>/dev/null
}

# The loader only finds plugins at <installed-plugins>/<bundle>/<plugin>/plugin.json,
# so that exact file is the only meaningful definition of "installed".
installed_ok() {
    [ -f "$DEST/fy27-territory-plan/plugin.json" ]
}

if [ -d "$DEST/.git" ]; then
    echo "-> Found an existing copy. Updating it..."
    git -C "$DEST" pull --quiet --ff-only 2>/dev/null
    # A pull reports success even if files were deleted or the checkout was
    # damaged, so re-clone whenever the result is not actually usable.
    if ! installed_ok; then
        echo "   That copy was damaged. Replacing it with a fresh one..."
        fetch_plugin
    fi
else
    echo "-> Downloading the plugin..."
    fetch_plugin
fi

if ! installed_ok; then
    echo ""
    echo "X  Download did not complete."
    echo "   Check your internet connection and run this again."
    echo "   If it keeps failing, send this to Rajeev:"
    echo "       missing $DEST/fy27-territory-plan/plugin.json"
    exit 1
fi

echo "-> Checking the Excel export component..."
if python3 -c "import xlsxwriter" >/dev/null 2>&1; then
    echo "   Already installed."
else
    python3 -m pip install --user --quiet xlsxwriter >/dev/null 2>&1
    if ! python3 -c "import xlsxwriter" >/dev/null 2>&1; then
        echo ""
        echo "!  The plugin is installed, but the Excel export component is not."
        echo "   Everything else will work. To fix it, run:"
        echo "       python3 -m pip install --user xlsxwriter"
        echo ""
    else
        echo "   Installed."
    fi
fi

echo "-> Checking the presentation component..."
if python3 -c "import pptx" >/dev/null 2>&1; then
    echo "   Already installed."
else
    python3 -m pip install --user --quiet python-pptx >/dev/null 2>&1
    if ! python3 -c "import pptx" >/dev/null 2>&1; then
        echo ""
        echo "!  The plugin is installed, but the presentation component is not."
        echo "   The territory plan will still work; only the H1 focus deck needs this."
        echo "   To fix it, run:"
        echo "       python3 -m pip install --user python-pptx"
        echo ""
    else
        echo "   Installed."
    fi
fi

echo ""
echo "==================================================="
echo " Done. Two more steps:"
echo ""
echo "   1. Quit the Copilot app completely and reopen it"
echo "   2. Type:  Build my FY27 territory plan"
echo ""
echo " Then, for the leadership presentation, type:"
echo "      Build my H1 focus accounts deck"
echo "==================================================="
echo ""
