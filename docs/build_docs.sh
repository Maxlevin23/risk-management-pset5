#!/bin/bash
# Rebuild the PDFs and Word files in docs/ from the Markdown sources.
# Needs pandoc and Google Chrome (used headless to print HTML to PDF).
cd "$(dirname "$0")" || exit 1
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
python3 make_code_listing.py
build() {  # build <name> <css>
  pandoc "$1.md" -s --embed-resources -c "css/$2.css" --metadata pagetitle="$1" \
    --syntax-highlighting=kate -o "/tmp/$1.html"
  "$CHROME" --headless --disable-gpu --no-pdf-header-footer \
    --print-to-pdf="$PWD/$1.pdf" "file:///tmp/$1.html" >/dev/null 2>&1
  pandoc "$1.md" -o "$1.docx"
  rm -f "/tmp/$1.html"
}
build Part1_Structure_and_Quirks part1
build Report doc
build AI_Appendix doc
build Problem5_Code code
"$CHROME" --headless --disable-gpu --no-pdf-header-footer --landscape \
  --print-to-pdf="$PWD/../output/verification_report.pdf" \
  "file://$PWD/../output/verification_report.html" >/dev/null 2>&1
