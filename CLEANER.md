# Content Cleaning Pipeline - Implementation Guide

## Overview

The content cleaning pipeline processes crawled pages from `knowledge_base/raw/`, removes unwanted elements, normalizes formatting, converts to clean markdown, and stores cleaned output in `knowledge_base/cleaned/`.

## Architecture

```
Raw Crawled Pages (JSON)
        ↓
   HTMLCleaner
   (Remove tags, scripts, ads, nav)
        ↓
   ContentCleaner
   (Normalize, validate, deduplicate)
        ↓
   MarkdownFormatter
   (Convert to markdown)
        ↓
   MetadataGenerator
   (Quality score, statistics)
        ↓
   Cleaned Pages (JSON + Markdown)
```

## Features Implemented

### ✅ HTML Cleaning
- Remove script tags and styles
- Remove navigation elements
- Remove footer content
- Remove advertisement containers
- Remove cookie banners
- Remove hidden elements
- Remove modals and popups

### ✅ Content Cleaning
- Whitespace normalization
- Duplicate paragraph detection
- Content validation
- Quality thresholds
- Boilerplate removal

### ✅ Markdown Conversion
- Heading hierarchy preservation (H1-H6)
- Table conversion to markdown
- List preservation (ordered/unordered)
- Link extraction and formatting
- Image metadata preservation
- Metadata section generation

### ✅ Metadata Generation
- Quality score calculation (0-1)
- Content statistics
- Preservation rate calculation
- Word and character counts
- Element counting (headings, lists, tables, links)
- Section categorization

### ✅ Output Format
- JSON format with full metadata
- Separate markdown file
- Statistics and quality metrics
- Preservation rates
- Original metadata preservation

## Components

### 1. HTMLCleaner (`crawler/cleaner.py`)

Removes unwanted HTML elements before parsing.

**Methods:**
- `clean_html()` - Remove navigation, ads, scripts, styles

**Removes:**
- Navigation elements (`<nav>`, `.nav`, `.navbar`)
- Footer content (`<footer>`, `[role="contentinfo"]`)
- Advertisements (`.ad`, `.advertisement`, `.banner`)
- Scripts (`<script>`, `<noscript>`)
- Styles (`<style>`)
- Cookie banners
- Modals and popups
- Hidden elements

### 2. ContentCleaner (`crawler/cleaner.py`)

Cleans and normalizes content.

**Methods:**
- `clean()` - Full cleaning pipeline
- `normalize_whitespace()` - Fix spacing and line breaks
- `validate_content()` - Quality validation
- `detect_duplicate_paragraphs()` - Find and remove duplicates

**Quality Thresholds:**
- Minimum 50 characters
- More text than numbers (2:1 ratio)
- Special characters < 30%

### 3. MarkdownFormatter (`crawler/formatter.py`)

Converts parsed content to clean markdown.

**Sub-components:**
- `HeadingNormalizer` - Convert heading hierarchy
- `TableConverter` - Convert tables to markdown
- `ListConverter` - Convert lists (UL/OL)
- `LinkConverter` - Format links section
- `ImageConverter` - Format images section

**Output Structure:**
1. Title (H1)
2. Description (italic)
3. Tags (bold)
4. Breadcrumb path
5. Main content (from body)
6. Tables (if any)
7. Lists (if any)
8. Images (if any)
9. Related links
10. Metadata section

### 4. PageCleaner (`crawler/page_cleaner.py`)

Orchestrates the cleaning process.

**Methods:**
- `clean_page()` - Clean a single page
- `clean_all_pages()` - Process all pages
- `save_cleaned_page()` - Save JSON and markdown
- `_generate_metadata()` - Create metadata
- `_generate_statistics()` - Calculate statistics
- `_calculate_quality_score()` - Score content (0-1)
- `_calculate_preservation_rate()` - Rate preservation

## Usage

### Command Line

```bash
# Clean all pages (uses default directories)
python clean_pages.py

# Specify custom directories
python clean_pages.py --raw-dir ./knowledge_base/raw --output-dir ./knowledge_base/cleaned

# Enable debug logging
python clean_pages.py --debug
```

### Python API

```python
from pathlib import Path
from crawler.page_cleaner import PageCleaner

# Initialize cleaner
cleaner = PageCleaner(
    raw_dir=Path("knowledge_base/raw"),
    cleaned_dir=Path("knowledge_base/cleaned")
)

# Clean all pages
stats = cleaner.clean_all_pages()

# Check statistics
print(f"Successful: {stats['successful']}")
print(f"Failed: {stats['failed']}")
print(f"Skipped: {stats['skipped']}")
```

## Output Format

### JSON Structure

```json
{
  "url": "https://example.edu/page",
  "title": "Page Title",
  "description": "Meta description",
  "keywords": ["tag1", "tag2"],
  "section": "category",
  "markdown": "# Full markdown content...",
  "metadata": {
    "url": "...",
    "title": "...",
    "section": "...",
    "source_metadata": {...},
    "content_statistics": {
      "word_count": 487,
      "character_count": 3254,
      "line_count": 89,
      "heading_count": 8,
      "list_count": 21,
      "table_count": 2,
      "link_count": 5
    },
    "quality_score": 0.95
  },
  "cleaned_at": "2024-07-02T19:35:25Z",
  "statistics": {
    "total_lines": 89,
    "non_empty_lines": 72,
    "total_paragraphs": 12,
    "avg_paragraph_length": 6.0,
    "total_words": 487,
    "total_characters": 3254,
    "preservation_rate": 0.92
  }
}
```

### Markdown File

Clean markdown with:
- Proper heading hierarchy
- Formatted tables
- Bullet lists
- Numbered lists
- Links with anchor text
- Images with alt text
- Metadata section

**Location**: `knowledge_base/cleaned/[filename].md`

## Quality Metrics

### Quality Score (0-1)

Based on:
- Title presence (+0.15)
- Description presence (+0.10)
- Keywords presence (+0.10)
- Content length (+0.15-0.25)
- Heading structure (+0.15)
- List presence (+0.10)
- Link presence (+0.10)

**Score = Sum of applicable factors (max 1.0)**

### Preservation Rate (0-1)

Measures how much original content was preserved.

Based on:
- Title preservation
- Heading preservation
- Table preservation
- List preservation
- Link preservation (minus removed ads/social media)

**Formula: preserved_elements / original_elements**

## Statistics Generated

For each cleaned page:

```
word_count              → Total words
character_count         → Total characters
line_count              → Total lines
non_empty_lines         → Non-blank lines
total_paragraphs        → Number of paragraphs
avg_paragraph_length    → Average paragraph size
heading_count           → H1-H6 headings
list_count              → List items
table_count             → Tables present
link_count              → Links present
quality_score           → 0-1 quality rating
preservation_rate       → 0-1 preservation
```

## File Organization

```
knowledge_base/
├── raw/                          # Original crawled pages
│   ├── index.json
│   ├── admissions.json
│   └── crawl_progress.json
├── cleaned/                      # Cleaned pages (output)
│   ├── index.json               # Metadata + markdown
│   ├── index.md                 # Pure markdown
│   ├── admissions.json
│   ├── admissions.md
│   └── example_cleaned_output.*
└── markdown/                     # Reserved for future
```

## Testing

```bash
# Run cleaner tests
pytest tests/test_cleaner.py -v

# Run with coverage
pytest tests/test_cleaner.py --cov=crawler

# Run specific test
pytest tests/test_cleaner.py::TestPageCleaner -v
```

## Performance

**Expected for 500 pages:**
- Processing time: 5-10 minutes
- Output size: Similar to input (1-2 GB)
- Memory usage: 100-200 MB

**Rates:**
- 1-2 pages per second
- Success rate: 95%+

## What Gets Removed

### Elements Removed
- `<script>` tags
- `<style>` tags
- `<noscript>` tags
- `<nav>` elements
- `<footer>` elements
- `[role="navigation"]`
- `[role="contentinfo"]`
- `.ad`, `.advertisement`, `.banner`
- `.cookie-notice`, `.gdpr`
- `.modal`, `.popup`, `.lightbox`
- Hidden elements (`display: none`)
- Tracking iframes

### Content Removed
- Duplicate paragraphs
- Excessive whitespace
- Cookie consent notices
- Newsletter subscription prompts
- Follow us (social media)
- Copyright notices
- Terms/Privacy links

### Preserved
- All headings
- All tables
- All lists
- All images (with alt text)
- All internal links
- Breadcrumb navigation
- Page metadata
- Original structure

## Examples

### Input (Raw JSON)
```json
{
  "url": "https://example.edu/page",
  "title": "Page",
  "body": "# Content\n\n...",
  "headings": [...],
  "tables": [...],
  ...
}
```

### Output (Cleaned JSON)
```json
{
  "url": "...",
  "markdown": "# Page\n\n...",
  "metadata": {
    "quality_score": 0.95,
    "content_statistics": {...},
    "preservation_rate": 0.92
  },
  "statistics": {...}
}
```

### Output (Markdown)
```markdown
# Page Title

*Description here*

**Tags:** tag1, tag2

**Path:** Home > Section

## Content Section

Regular paragraph text.

### Subsection

- List item 1
- List item 2

| Header | Column |
|--------|--------|
| Data   | Value  |
```

## Troubleshooting

### No pages being cleaned

1. Check `knowledge_base/raw/` exists and has files
2. Verify raw files are valid JSON
3. Check logs: `tail -f logs/app.log`
4. Try with `--debug` flag

### Quality score too low

- Page has insufficient content (< 500 chars)
- Missing title or description
- Not enough structured elements

### Preservation rate low

- Original page had few elements
- Many ads/social media removed
- Boilerplate was significant

### Memory usage high

- Large pages with extensive metadata
- Many images
- Large tables

**Solution:** Process in batches or reduce MAX_PAGES

## Next Steps

After cleaning:

1. **Review cleaned pages** - Check `knowledge_base/cleaned/`
2. **Verify quality scores** - Look for scores > 0.75
3. **Check statistics** - Review preservation rates
4. **Proceed to chunking** - Split into semantic chunks
5. **Generate embeddings** - Create vector representations
6. **Index in ChromaDB** - Store in vector database

## Integration with Pipeline

```
Crawling (knowledge_base/raw/)
    ↓
Cleaning (this module)
    ↓
Chunking (ingestion/chunker.py)
    ↓
Embedding (ingestion/embedder.py)
    ↓
Indexing (ingestion/index.py)
    ↓
Retrieval (retriever/retriever.py)
    ↓
Chatbot (chatbot/chatbot.py)
```

## References

- [Example cleaned output](knowledge_base/cleaned/example_cleaned_output.json)
- [Example markdown](knowledge_base/cleaned/example_cleaned_output.md)
- [Test suite](tests/test_cleaner.py)
