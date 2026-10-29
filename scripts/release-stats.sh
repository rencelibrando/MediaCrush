#!/usr/bin/env bash
# =============================================================================
# MediaCrush Release Analytics Tracker
# Fetches live download counts and asset breakdown from GitHub Releases API
# =============================================================================

REPO="rencelibrando/MediaCrush"
API_URL="https://api.github.com/repos/${REPO}/releases"

echo "=========================================================="
echo "  MediaCrush Release Analytics (${REPO})"
echo "=========================================================="
echo ""

DATA=$(curl -s "${API_URL}")

# Check if releases exist or API rate limited
if echo "$DATA" | grep -q '"message":'; then
  MSG=$(echo "$DATA" | grep -o '"message": "[^"]*"' | head -n 1)
  echo "GitHub API Notice: $MSG"
  exit 0
fi

python3 -c "
import json, sys

try:
    releases = json.loads('''$DATA''')
    if not releases:
        print('No releases published yet.')
        sys.exit(0)

    grand_total = 0

    for rel in releases:
        tag = rel.get('tag_name', 'Unknown')
        name = rel.get('name', tag)
        created = rel.get('published_at', '')[:10]
        assets = rel.get('assets', [])

        print(f'Release: {name} ({tag}) — Published: {created}')
        print(f'   URL: {rel.get(\"html_url\", \"\")}')
        print('   ' + '-' * 54)

        rel_total = 0
        if not assets:
            print('   (No assets uploaded)')
        else:
            for a in assets:
                filename = a.get('name', '')
                count = a.get('download_count', 0)
                size_mb = round(a.get('size', 0) / (1024 * 1024), 2)
                rel_total += count
                print(f'   • {filename:<34} {size_mb:>6} MB  |  {count:>4} downloads')

        grand_total += rel_total
        print('   ' + '-' * 54)
        print(f'   Subtotal for {tag}: {rel_total} downloads\n')

    print('==========================================================')
    print(f'   GRAND TOTAL DOWNLOADS: {grand_total}')
    print('==========================================================')

except Exception as e:
    print(f'Error parsing release data: {e}')
"
