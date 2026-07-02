# Quick Start - Content Cleaning Pipeline

## What It Does

Cleans crawled content and converts to markdown:
- ✅ Removes navigation, footers, ads
- ✅ Normalizes formatting
- ✅ Converts to clean markdown
- ✅ Generates metadata & quality scores
- ✅ Stores in `knowledge_base/cleaned/`

## 2-Minute Setup

### Step 1: Check Prerequisites
```bash
# Verify you have crawled pages
ls knowledge_base/raw/ | head -5
# Should show: index.json, admissions.json, etc.
```

### Step 2: Run Cleaner
```bash
python clean_pages.py
```

Done! Output goes to `knowledge_base/cleaned/`

## What You Get

**Per page:**
- `filename.json` - Full metadata + markdown
- `filename.md` - Pure markdown file

**Example structure:**
```
# Page Title

*Description*

**Tags:** tag1, tag2

## Sections

- Lists
- Are preserved
- With formatting

| Tables | Preserved |
|--------|-----------|
| Row 1  | Data      |

---

**Metadata:** Author, Published, Modified
```

## Monitor Progress

```bash
# Watch in real-time
tail -f logs/app.log

# Check output
ls knowledge_base/cleaned/ | wc -l

# View a cleaned page
cat knowledge_base/cleaned/index.md | head -50
```

## Configuration

Default behavior:
- Input: `knowledge_base/raw/`
- Output: `knowledge_base/cleaned/`

Custom directories:
```bash
python clean_pages.py --raw-dir ./raw --output-dir ./output
```

Debug mode:
```bash
python clean_pages.py --debug
```

## Output Formats

### JSON (Metadata)
```json
{
  "url": "...",
  "markdown": "# Full markdown content",
  "metadata": {
    "quality_score": 0.95,
    "content_statistics": {
      "word_count": 487,
      "heading_count": 8,
      "table_count": 2,
      "link_count": 5
    },
    "preservation_rate": 0.92
  },
  "statistics": {...}
}
```

### Markdown (Clean Content)
```markdown
# Title

**Description**

## Main Content

Content here...

| Tables | Formatted |
|--------|-----------|

---

## Related Links

[Link text](url)
```

## Quality Metrics

**Quality Score (0-1):**
- 0.9+ : Excellent
- 0.75-0.89: Good
- 0.5-0.74: Fair
- <0.5: Poor

**Preservation Rate:**
- Tracks how much original content was kept
- 0.9+ : Excellent
- 0.75+ : Good

## Verify Output

```bash
# Check statistics
python -c "
import json
data = json.load(open('knowledge_base/cleaned/index.json'))
print(f\"Quality: {data['metadata']['quality_score']}\")
print(f\"Words: {data['metadata']['content_statistics']['word_count']}\")
print(f\"Preserved: {data['statistics']['preservation_rate']}\")
"

# Count cleaned pages
find knowledge_base/cleaned -name "*.md" | wc -l

# View sample cleaned page
head -100 knowledge_base/cleaned/admissions.md
```

## What Gets Removed

✅ Removed:
- Navigation menus
- Footer content
- Ads and banners
- Cookie notices
- Scripts and styles
- Duplicate paragraphs
- Hidden elements

✅ Preserved:
- Heading hierarchy
- Tables
- Lists
- Links
- Images
- Metadata

## Troubleshooting

### No files being cleaned

**Problem:** "Found 0 pages to clean"

**Solution:**
```bash
# Check raw directory exists
ls knowledge_base/raw/

# Must have JSON files (not .md)
ls knowledge_base/raw/*.json

# If empty, run crawler first
python crawl_website.py https://your-college.edu
```

### Low quality scores

**Problem:** Quality scores < 0.5

**Possible causes:**
- Pages too short (<200 words)
- Missing title/description
- Lots of boilerplate removed

**Solution:**
- This is normal for header/footer pages
- Focus on pages with scores > 0.75

### Output too large

**Problem:** Markdown files too big

**Solution:**
- Content chunking comes next
- Large files are fine for now
- Chunker will split them

## Next Steps

After cleaning:

1. **Review sample pages**
   ```bash
   cat knowledge_base/cleaned/index.md
   ```

2. **Check statistics**
   ```bash
   find knowledge_base/cleaned -name "*.json" | head -1 | xargs cat | python -m json.tool
   ```

3. **Count pages cleaned**
   ```bash
   ls knowledge_base/cleaned/*.md | wc -l
   ```

4. **Proceed to chunking** (next phase)
   ```bash
   python chunk_documents.py
   ```

## Statistics Summary

After cleaning, check:

```
Total Pages Cleaned: 445
Success Rate: 95%
Avg Quality Score: 0.87
Avg Preservation: 0.89
Avg Word Count: 487
Avg Heading Count: 8
Avg Table Count: 1
Avg Link Count: 5
```

## Common Output Files

```
knowledge_base/cleaned/
├── index.json              # Homepage
├── index.md
├── admissions.json         # Admissions page
├── admissions.md
├── programs_cs.json        # Programs
├── programs_cs.md
├── contact.json            # Contact
├── contact.md
└── example_cleaned_output.*  # Example files
```

## Monitoring Output

```bash
# Watch progress
watch -n 2 'ls knowledge_base/cleaned/*.md | wc -l'

# Check quality scores
find knowledge_base/cleaned -name "*.json" -exec grep -h quality_score {} \; | sort | uniq -c

# Find low-quality pages
find knowledge_base/cleaned -name "*.json" -exec \
  python -c "import sys, json; d=json.load(open(sys.argv[1])); d['metadata']['quality_score'] < 0.7 and print(sys.argv[1])" {} \;
```

## Tips

1. **Start small** - First 50 pages to verify output
2. **Check logs** - `tail -f logs/app.log` for details
3. **Verify quality** - Spot-check some markdown files
4. **Monitor memory** - Should be <200MB for 500 pages

## Example Commands

```bash
# Basic cleanup (all pages)
python clean_pages.py

# Debug mode (verbose logging)
python clean_pages.py --debug

# Custom input/output
python clean_pages.py \
  --raw-dir knowledge_base/raw \
  --output-dir knowledge_base/cleaned

# Check results
ls knowledge_base/cleaned/*.md | wc -l
head -50 knowledge_base/cleaned/index.md
cat knowledge_base/cleaned/index.json | python -m json.tool
```

---

**For detailed docs**: See [CLEANER.md](CLEANER.md)
