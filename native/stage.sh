#!/bin/bash
# Stage the web app for the native iOS shell.
#
# Copies docs/ (the PWA) into native/www, EXCLUDING:
#   - data/        (~36 MB; the native app fetches live data from GitHub Pages
#                   instead, so inventory stays fresh without an app update)
#   - sw.js        (service workers don't run on the capacitor:// scheme)
# Run this before every `npx cap sync ios`.
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf native/www
mkdir -p native/www
rsync -a --exclude 'data/' --exclude 'sw.js' --exclude '.DS_Store' docs/ native/www/
echo "Staged $(find native/www -type f | wc -l | tr -d ' ') files into native/www"
