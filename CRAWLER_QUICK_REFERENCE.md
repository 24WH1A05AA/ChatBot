# Website Crawler - Quick Reference Card

## 🚀 Quick Start (3 steps)

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env: Add COLLEGE_WEBSITE_URL

# 3. Run
python crawl_website.py https://your-college.edu
```

## 📊 Output Example

```
knowledge_base/raw/admissions_apply.json
{
  "url": "https://college.edu/admissions/apply",
  "title": "Apply for Admission",
  "section": "admissions",
  "body": "Markdown formatted content...",
  "links": [...], "images": [...], "metadata": {...}
}
```

## ⚙️ Configuration (.env)

```env
COLLEGE_WEBSITE_URL=https://your-college.edu
CRAWL_DEPTH=5              # 1-20 levels
MAX_PAGES=1000            # Maximum pages
REQUEST_TIMEOUT=30        # Seconds
LOG_LEVEL=INFO            # DEBUG, INFO, WARNING, ERROR
```

## 📁 Directory Structure

```
knowledge_base/raw/       ← Crawled pages (JSON)
  ├─ index.json
  ├─ admissions.json
  └─ crawl_progress.json   ← Auto-saved progress

logs/app.log              ← Application logs
```

## 🔍 Monitoring

```bash
# Watch progress
tail -f logs/app.log

# Check statistics
cat knowledge_base/raw/crawl_progress.json | python -m json.tool

# Count pages
ls knowledge_base/raw/*.json | wc -l

# View a page
cat knowledge_base/raw/index.json | python -m json.tool
```

## 📝 Features

| Feature | Status |
|---------|--------|
| Recursive crawling | ✅ |
| JS rendering | ✅ |
| Duplicate detection | ✅ |
| Progress saving | ✅ |
| Resume capability | ✅ |
| Metadata extraction | ✅ |
| Link extraction | ✅ |
| Image extraction | ✅ |
| Content cleaning | ✅ |
| Error tracking | ✅ |

## 🧪 Testing

```bash
# Run tests
pytest tests/test_crawler.py -v

# Run with coverage
pytest tests/test_crawler.py --cov=crawler
```

## 📚 Documentation

| File | Purpose |
|------|---------|
| CRAWLER.md | Technical reference |
| QUICKSTART_CRAWLER.md | 5-minute setup |
| CRAWLER_IMPLEMENTATION.md | Architecture |
| VERIFICATION_CHECKLIST.md | Verification |

## 💡 Tips

1. **Test first**: Run with `CRAWL_DEPTH=1` before full crawl
2. **Monitor logs**: Use `tail -f logs/app.log` to watch progress
3. **Resume anytime**: Just run the same command again
4. **Debug mode**: Set `LOG_LEVEL=DEBUG` for verbose output
5. **Lower memory**: Reduce `MAX_PAGES` if needed

## 🔧 Troubleshooting

### Crawler not starting?
```bash
# Check configuration
python -c "from config import get_settings; print(get_settings())"

# Run with debug
LOG_LEVEL=DEBUG python crawl_website.py <url>
```

### Low page count?
- Check network connectivity
- Verify website is accessible
- Increase `REQUEST_TIMEOUT`
- Reduce `CRAWL_DEPTH` for faster testing

### High memory usage?
- Reduce `MAX_PAGES`
- Reduce `CRAWL_DEPTH`
- Close other applications

## 📊 Performance

**Expected for 500 pages:**
- Time: 20-30 minutes
- Storage: 2-5 GB
- Memory: 500 MB - 1 GB

## 🎯 Next Steps

After crawling:
1. Review pages in `knowledge_base/raw/`
2. Check statistics in `crawl_progress.json`
3. Proceed to document chunking
4. Generate embeddings
5. Index in ChromaDB
6. Build retriever
7. Connect to chatbot

## 📞 Common Commands

```bash
# Run crawler
python crawl_website.py https://your-college.edu

# Resume interrupted crawl
python crawl_website.py https://your-college.edu

# Check logs
tail -f logs/app.log

# Check progress
cat knowledge_base/raw/crawl_progress.json

# List crawled pages
ls knowledge_base/raw/ | grep -v progress | wc -l

# View page details
python -c "import json; print(json.dumps(json.load(open('knowledge_base/raw/index.json')), indent=2))" | head -50
```

## 🔑 Key Classes

| Class | File | Purpose |
|-------|------|---------|
| CrawlerOrchestrator | crawler/crawl.py | Main coordinator |
| SitemapParser | crawler/sitemap.py | Sitemap discovery |
| HTMLParser | crawler/parser.py | Content extraction |
| ContentCleaner | crawler/cleaner.py | Data cleaning |
| MetadataExtractor | crawler/metadata.py | Metadata collection |

## 📋 Output Fields (per page)

```
url                 → Source URL
title               → Page title
description         → Meta description
keywords            → Meta keywords
breadcrumb          → Navigation path
section             → Inferred category
headings            → Heading hierarchy
body                → Markdown content
tables              → Structured tables
lists               → Lists (ul/ol)
images              → Images with alt text
links               → Links with text
metadata            → Rich metadata
crawled_at          → Timestamp
status_code         → HTTP status
```

## 🚨 Error Handling

Failed pages tracked in: `crawl_progress.json`

```json
{
  "failed_urls": {
    "https://broken-url.com": "Error message"
  }
}
```

Can retry manually or they'll be skipped on resume.

---

**For detailed docs**: See CRAWLER.md or QUICKSTART_CRAWLER.md
