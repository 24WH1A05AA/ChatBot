# Crawler File Download Extension - Implementation Guide

## Overview

The crawler extension adds automatic file detection, download, and processing capabilities to the web crawler. It automatically identifies downloadable files (PDF, DOCX, TXT, CSV), downloads them, extracts content, converts to markdown, and associates them with source pages.

## Architecture

```
Crawled Pages (HTML)
        ↓
FileDetector
(Identify download links)
        ↓
FileDownloader
(Async download with deduplication)
        ↓
FileExtractor
(Extract content by file type)
        ↓
FileDocumentConverter
(Convert to markdown)
        ↓
FileAssociationTracker
(Link files to source pages)
        ↓
Knowledge Base
(knowledge_base/documents/)
```

## Components

### 1. FileDetector (`crawler/file_detector.py`)
**Detects downloadable files**
- Regex-based link extraction
- Support for PDF, DOCX, DOC, TXT, CSV, XLSX, PPTX
- Query parameter handling
- Extension and MIME type identification

**Methods:**
- `detect_files_in_html()` - Parse HTML for download links
- `detect_files_in_links()` - Extract files from link objects
- `is_supported_format()` - Check if format is supported
- `filter_by_type()` - Filter files by extension

### 2. FileExtractor (`crawler/file_extractor.py`)
**Extracts content from files**
- PDF extraction with PyPDF2
- DOCX extraction with python-docx
- TXT file reading
- CSV to markdown table conversion

**Supported Formats:**
- PDF: Page-by-page extraction
- DOCX: Paragraphs, tables, formatted text
- TXT: Plain text
- CSV: Markdown table format

**Methods:**
- `extract()` - Extract content
- `extract_metadata()` - Get file metadata
- Type-specific extractors

### 3. FileDownloader (`crawler/file_downloader.py`)
**Async file downloading with deduplication**
- Async HTTP with aiohttp
- SHA256-based duplicate prevention
- Concurrent download support
- Local file caching

**Features:**
- Hash-based deduplication
- Automatic filename collision handling
- File organization by type
- Metadata persistence

**Methods:**
- `download()` - Download single file
- `download_batch()` - Concurrent downloads
- `is_duplicate()` - Check for duplicates
- `get_statistics()` - Download stats

### 4. FileDocumentConverter (`crawler/file_converter.py`)
**Converts file content to markdown**
- Structured markdown generation
- Metadata section creation
- File size formatting
- Batch conversion support

**Output Structure:**
```markdown
# filename.ext

## Document Information
- Type, Size, URL, Source Page

## Document Metadata
- Title, Author, Created, Modified, Pages

## Content
[Extracted content here]
```

### 5. FileAssociationTracker (`crawler/file_association.py`)
**Tracks file-to-page associations**
- Bidirectional mapping
- File-to-pages tracking
- Page-to-files tracking
- Persistent storage

**Methods:**
- `associate()` - Link file to page
- `get_pages_for_file()` - Find pages with file
- `get_files_for_page()` - Find files on page
- `get_statistics()` - Association stats

### 6. CrawlerFileExtension (`crawler/file_extension.py`)
**Main orchestrator for file processing**
- Coordinates all file operations
- Integrates with crawler
- Manages statistics
- Handles batch processing

**Methods:**
- `process_page_files()` - Process files from page
- `get_statistics()` - Overall stats
- `get_files_for_page()` - Page file lookup
- `get_pages_for_file()` - File page lookup

## Usage

### Integration with Crawler

```python
from crawler.crawl import CrawlerOrchestrator
from crawler.file_extension import CrawlerFileExtension

# Create crawler
crawler = CrawlerOrchestrator()

# Add file support
file_ext = CrawlerFileExtension()

# When processing a page
for page_url, page_data in crawled_pages.items():
    # Process files
    documents = await file_ext.process_page_files(page_url, page_data)
```

### Direct Usage

```python
from crawler.file_detector import FileDetector
from crawler.file_downloader import FileDownloader
from crawler.file_converter import FileDocumentConverter

# Detect files
detector = FileDetector()
files = detector.detect_files_in_links(links, base_url)

# Download
downloader = FileDownloader()
downloaded = await downloader.download_batch(
    [f["url"] for f in files],
    base_url
)

# Convert
converter = FileDocumentConverter()
for doc_file in downloaded:
    markdown_doc = converter.convert(
        Path(doc_file["local_path"]),
        doc_file["file_type"],
        doc_file
    )
```

## Supported File Types

| Format | Extension | Extraction | Metadata | Markdown |
|--------|-----------|-----------|----------|----------|
| PDF | .pdf | PyPDF2 | Pages, Author, Title | ✅ |
| DOCX | .docx | python-docx | Paragraphs, Tables | ✅ |
| DOC | .doc | python-docx | Paragraphs, Tables | ✅ |
| TXT | .txt | Native | - | ✅ |
| CSV | .csv | Native | Columns, Rows | ✅ |
| XLSX | .xlsx | Read only | Columns | Planned |
| PPTX | .pptx | Read only | Slides | Planned |

## Output Structure

### File Storage
```
knowledge_base/
├── downloads/              # Cached downloads
│   ├── pdf/               # PDF files
│   ├── docx/              # DOCX files
│   ├── txt/               # TXT files
│   ├── csv/               # CSV files
│   └── download_metadata.json
└── documents/             # Converted documents
    ├── document1.json
    ├── document2.json
    └── ...
```

### Document Format (JSON)
```json
{
  "url": "Original file URL",
  "filename": "original_filename.ext",
  "file_type": "pdf",
  "title": "Document title",
  "source_page": "URL where found",
  "markdown": "# Full markdown content...",
  "metadata": {
    "author": "...",
    "pages": 5,
    "created": "...",
    ...
  },
  "file_info": {...},
  "converted_at": "ISO timestamp"
}
```

## Deduplication

**Hash-Based Prevention:**
- SHA256 hash of file content
- Prevents duplicate downloads
- Tracks across all pages
- Persistent storage

**Efficiency:**
- Single network request per unique file
- Reduced storage usage
- Fast lookup (set-based)

## Performance

**Expected for 500 pages with files:**
- Detection: 1-2 seconds per page
- Download: 100-500 KB/s (network dependent)
- Extraction: 0.5-2 seconds per file
- Conversion: 0.1-0.5 seconds per file
- Memory: Additional 100-200 MB

**Concurrent Downloads:**
- Default: 5 concurrent downloads
- Configurable max_concurrent parameter
- Optimized for 1-50 MB files

## Statistics

The extension tracks:

**Detection:**
- Total files detected
- Files by type
- Files per page

**Download:**
- Successfully downloaded
- Failed downloads
- Duplicate skipped
- Total size by type

**Conversion:**
- Successfully converted
- Failed conversions
- Documents by type

**Association:**
- Total unique files
- Total pages with files
- Total associations
- Files per page mapping

## Error Handling

**Graceful Degradation:**
- Failed download doesn't stop crawl
- Failed extraction continues with next file
- Missing dependencies logged clearly
- Partial results returned

**Logging:**
- All operations logged
- Error details provided
- Statistics tracked
- Progress reported

## Dependencies

**New Requirements:**
- PyPDF2==4.0.1 (PDF extraction)
- python-docx==0.8.11 (DOCX extraction)

**Already Included:**
- aiohttp (async downloads)
- pathlib (file operations)

## Integration Points

### With Main Crawler
```python
# In CrawlerOrchestrator.crawl()
file_ext = CrawlerFileExtension()

# When saving each page
await file_ext.process_page_files(url, page_data)

# Get statistics
stats = file_ext.get_statistics()
```

### With Cleaner
Files are converted to markdown, compatible with cleaning pipeline:
```
Downloaded Files → Markdown Documents → Clean Pipeline → Knowledge Base
```

### With Indexing
Converted markdown documents can be indexed like crawler output:
```
Documents → Chunking → Embedding → ChromaDB
```

## Configuration

Environment variables (in .env):
```env
# Optional: Custom download cache location
FILE_CACHE_DIR=knowledge_base/downloads

# Optional: Custom output location
FILE_OUTPUT_DIR=knowledge_base/documents

# Optional: Max concurrent downloads
FILE_MAX_CONCURRENT=5

# Optional: Download timeout
FILE_TIMEOUT=30
```

## Troubleshooting

### Missing Dependencies
```bash
pip install PyPDF2 python-docx
```

### Extraction Issues
**PDF:** Check if corrupted or password-protected
**DOCX:** Verify file is valid Office format
**CSV:** Ensure proper encoding (UTF-8)

### Download Failures
- Check network connectivity
- Verify URL accessibility
- Check file permissions
- Review logs for details

### Memory Issues
- Reduce max_concurrent downloads
- Process in smaller batches
- Monitor PDF file sizes

## Examples

### Example Detected Files
```json
{
  "url": "https://college.edu/docs/requirements.pdf",
  "filename": "requirements.pdf",
  "extension": "pdf",
  "mime_type": "application/pdf"
}
```

### Example Downloaded File
```json
{
  "url": "https://college.edu/docs/requirements.pdf",
  "filename": "requirements.pdf",
  "local_path": "knowledge_base/downloads/pdf/requirements.pdf",
  "file_type": "pdf",
  "file_size": 245000,
  "hash": "abc123...",
  "source_page": "https://college.edu/admissions",
  "downloaded_at": "2024-07-02T19:42:07Z"
}
```

### Example Converted Document
```json
{
  "url": "https://college.edu/docs/requirements.pdf",
  "filename": "requirements.pdf",
  "markdown": "# requirements.pdf\n\n## Document Information\n...",
  "metadata": {
    "pages": 5,
    "author": "Admissions"
  }
}
```

## Next Steps

1. **Run crawler with file support**
   ```bash
   python crawl_website.py https://your-college.edu
   ```

2. **Review downloaded files**
   ```bash
   ls knowledge_base/downloads/
   ```

3. **Check converted documents**
   ```bash
   ls knowledge_base/documents/
   ```

4. **Process with cleaner**
   ```bash
   python clean_pages.py
   ```

5. **Index in knowledge base**
   ```bash
   python index_documents.py
   ```

## References

- [FileDetector](crawler/file_detector.py)
- [FileExtractor](crawler/file_extractor.py)
- [FileDownloader](crawler/file_downloader.py)
- [FileConverter](crawler/file_converter.py)
- [FileAssociation](crawler/file_association.py)
- [FileExtension](crawler/file_extension.py)
- [Tests](tests/test_file_handling.py)
