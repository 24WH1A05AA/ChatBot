# Quick Start Guide - Website Crawler

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
cp .env.example .env
```

Edit `.env` file and set:
```env
OPENAI_API_KEY=your_api_key_here          # Required for OpenAI (used later)
COLLEGE_WEBSITE_URL=https://your-college.edu
CRAWL_DEPTH=5                             # 1-20 levels
MAX_PAGES=1000                            # Maximum pages to crawl
LOG_LEVEL=INFO                            # DEBUG for verbose output
```

### Step 3: Run the Crawler
```bash
python crawl_website.py https://your-college.edu
```

That's it! The crawler will:
1. ✅ Discover URLs from sitemaps
2. ✅ Crawl recursively up to 5 levels deep
3. ✅ Extract all content and metadata
4. ✅ Save each page as JSON
5. ✅ Track progress and failed URLs

## Output

All crawled pages saved in: `knowledge_base/raw/`

Example file: `index.json`, `admissions.json`, `programs_cs.json`, etc.

Each JSON file contains:
- Page content (in markdown)
- Metadata (title, description, keywords)
- Extracted resources (images, links, tables)
- Navigation info (breadcrumbs)
- Crawl timestamp and status

## Monitoring Progress

Watch the console output:
```
INFO: Processing depth 0, 1 URLs in queue
INFO: Crawling: https://your-college.edu
INFO: Successfully crawled: https://your-college.edu
INFO: Saved page to: knowledge_base/raw/index.json
...
```

Check progress file:
```bash
cat knowledge_base/raw/crawl_progress.json
```

## Resume Interrupted Crawls

If the crawler is interrupted, just run it again:
```bash
python crawl_website.py https://your-college.edu
```

It automatically resumes from where it left off (stored in `crawl_progress.json`).

## Troubleshooting

### Nothing is crawling?
```bash
# Check if URL is valid
python -c "from urllib.parse import urlparse; print(urlparse('https://your-college.edu'))"

# Try with DEBUG logging
# Edit .env: LOG_LEVEL=DEBUG
# Then run again
```

### Crawler is too slow?
```env
# Reduce depth
CRAWL_DEPTH=2

# Reduce max pages
MAX_PAGES=100

# Increase timeout (may help)
REQUEST_TIMEOUT=60
```

### Running out of disk space?
Check disk usage:
```bash
du -sh knowledge_base/raw/
```

The output is typically:
- 500 pages → 1-2 GB
- 1000 pages → 2-5 GB

## Next Steps

After successful crawl:

1. **Review the output**
   ```bash
   ls -la knowledge_base/raw/ | head -20
   cat knowledge_base/raw/index.json | python -m json.tool | head -50
   ```

2. **Check statistics**
   ```bash
   cat knowledge_base/raw/crawl_progress.json
   ```

3. **Next phase: Document Chunking**
   - Coming next: Split documents into chunks
   - Then: Generate embeddings
   - Then: Index in ChromaDB
   - Finally: Q&A with the chatbot

## Tips & Tricks

### Test with a single page first
```python
from crawler.crawl import CrawlerOrchestrator
import asyncio

async def test():
    crawler = CrawlerOrchestrator()
    # This will test the full depth=1
    await crawler.crawl("https://your-college.edu")
    stats = crawler.get_statistics()
    print(f"Crawled {stats['total_urls_crawled']} pages")

asyncio.run(test())
```

### Check for failed URLs
```bash
python -c "import json; data = json.load(open('knowledge_base/raw/crawl_progress.json')); print('\n'.join(data.get('failed_urls', {}).keys()))"
```

### Count crawled pages
```bash
ls knowledge_base/raw/*.json | wc -l
```

### View a specific page
```bash
cat knowledge_base/raw/admissions.json | python -m json.tool
```

## Expected Output

```
INFO: === College FAQ Chatbot - Website Crawler ===
INFO: Start URL: https://example-college.edu
INFO: Max Depth: 5
INFO: Max Pages: 1000

INFO: Discovering sitemaps...
INFO: Found 150 URLs in https://example-college.edu/sitemap.xml

INFO: Processing depth 0, 1 URLs in queue
INFO: Crawling: https://example-college.edu
INFO: Successfully crawled: https://example-college.edu
INFO: Extracted 45 internal links from https://example-college.edu
INFO: Saved page to: knowledge_base/raw/index.json

... [many more pages] ...

INFO: === Crawl Statistics ===
INFO: Total URLs Found: 450
INFO: Total URLs Crawled: 445
INFO: Total URLs Failed: 5
INFO: Pages Saved: 445
INFO: Start Time: 2024-07-02T16:15:00Z
INFO: End Time: 2024-07-02T18:30:00Z

INFO: Crawl completed successfully!
```

## Support

For detailed documentation, see:
- `CRAWLER.md` - Complete reference guide
- `CRAWLER_IMPLEMENTATION.md` - Architecture and features
- `README.md` - Project overview

## Questions?

Check the logs:
```bash
tail -f logs/app.log
```

Enable debug mode for more details:
```env
LOG_LEVEL=DEBUG
```

Happy crawling! 🕷️
