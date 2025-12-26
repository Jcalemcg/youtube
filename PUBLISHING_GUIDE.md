# Advanced Export & Publishing Guide

## Overview

The Advanced Export & Publishing system provides comprehensive functionality to export articles in multiple formats and publish them to various platforms including Medium.

## Features

### 📥 Export Formats

The system supports exporting articles in the following formats:

#### 1. **Markdown** (.md)
- Clean, readable format
- Perfect for version control and editing
- Includes article metadata and SEO information
- Best for: Documentation, GitHub, version control

#### 2. **JSON** (.json)
- Complete structured data export
- Includes all pipeline stages (transcript, analysis, article, SEO)
- Ideal for programmatic access and data archiving
- Best for: Data integration, archival, automation

#### 3. **HTML** (.html)
- Self-contained web page
- Professional styling with responsive design
- Includes metadata and article information
- Supports printing and sharing
- Best for: Web publishing, sharing, viewing in browser

#### 4. **CSV** (.csv)
- Spreadsheet-compatible format
- Organized by content type and sections
- Easy to import into Excel or Google Sheets
- Best for: Data analysis, spreadsheet tools, reporting

### 📤 Publishing Platforms

#### Medium
Publish articles directly to Medium with full integration:
- Automatic drafting or publishing
- Tag management
- Canonical URL support
- Subscriber notifications
- SEO metadata mapping

## Installation & Setup

### 1. Install Dependencies

The publishing system requires the following dependencies (already included):
- `requests` - For API calls
- `markdown` - For format conversion
- `pydantic` - For data validation

### 2. Configure API Tokens

#### Medium Integration

To publish to Medium, you need an integration token:

1. Visit [Medium Account Settings](https://medium.com/me/settings)
2. Scroll to "Integration tokens"
3. Generate a new token
4. Copy the token (keep it secure!)
5. Use it in the Streamlit UI or programmatically

## Usage

### Using the Streamlit UI

The Streamlit application includes built-in export and publishing functionality:

1. **Export Section**: Located in the final stage
   - Select desired export formats
   - Click "Export Now"
   - Download files directly

2. **Publishing Section**: Located below export
   - Select publishing platform
   - Enter platform API credentials
   - Configure publishing options
   - Click publish button

### Programmatic Usage

```python
from pathlib import Path
from youtube_to_article.publishing.manager import PublishingManager
from youtube_to_article.publishers.base import PublishConfig, PublishingPlatform
from youtube_to_article.models.schemas import FinalOutput

# Initialize manager
manager = PublishingManager(output_dir=Path("./output"))

# Export in multiple formats
exports = manager.export(
    final_output,
    formats=["markdown", "json", "html"]
)

# Or export single format
html_path = manager.export_single(
    final_output,
    format="html"
)

# Publish to Medium
from youtube_to_article.publishers.medium import MediumPublisher

publisher = MediumPublisher(api_token="your_medium_token")
manager.register_publisher("medium", publisher)

config = PublishConfig(
    platform=PublishingPlatform.MEDIUM,
    draft=True,
    tags=["python", "ai", "content"],
    canonical_url="https://youtube.com/watch?v=..."
)

result = manager.publish(final_output, "medium", config)
print(f"Published to: {result.url}")
```

### Combined Export & Publish

```python
from youtube_to_article.publishers.base import PublishConfig, PublishingPlatform

result = manager.export_and_publish(
    final_output,
    export_formats=["markdown", "html"],
    publish_to=[
        ("medium", PublishConfig(
            platform=PublishingPlatform.MEDIUM,
            draft=True,
            tags=["article"]
        ))
    ]
)

print(f"Exports: {result['exports']}")
print(f"Publishing: {result['publishing']}")
```

## Publishing Configuration

### PublishConfig Options

```python
PublishConfig(
    platform=PublishingPlatform.MEDIUM,  # Required: target platform
    draft=True,                           # Optional: publish as draft (default: True)
    tags=["python", "ai"],               # Optional: article tags (max 5 for Medium)
    canonical_url="https://...",         # Optional: original URL for SEO
    schedule_time=datetime(...),         # Optional: scheduled publish time
    notify_subscribers=True,              # Optional: notify followers
    custom_metadata={...}                 # Optional: platform-specific data
)
```

### Medium-Specific Settings

- **Draft Mode**: Publish as draft for review before making live
- **Tags**: Up to 5 tags per article; keywords are automatically added
- **Canonical URL**: Points search engines to original content
- **Notify Subscribers**: Send notification to your Medium followers

## Publishing History

All publishing attempts are tracked and stored:

### Accessing History

```python
# Load history for specific article
history = manager.get_publishing_history(
    video_id="dQw4w9WgXcQ",
    article_slug="never-gonna-give-you-up"
)

# View all results
for result in history.results:
    print(f"{result.platform}: {result.status}")
    if result.url:
        print(f"  URL: {result.url}")
    if result.error:
        print(f"  Error: {result.error}")

# Get overall statistics
stats = manager.get_statistics()
print(f"Total publishes: {stats['total_publishes']}")
print(f"By platform: {stats['by_platform']}")
print(f"By status: {stats['by_status']}")
```

### History File Structure

Publishing history is saved in JSON format:
```
output/
└── publishing_history/
    ├── video_id_1_slug_1_history.json
    ├── video_id_2_slug_2_history.json
    └── ...
```

## Export File Structure

Exported files are organized by format:

```
output/
├── article_slug.md          # Markdown format
├── article_slug.json        # JSON format
├── article_slug.html        # HTML format
└── article_slug.csv         # CSV format
```

## Error Handling

The system includes comprehensive error handling:

```python
# Check publishing result
result = manager.publish(final_output, "medium", config)

if result.status == PublishingStatus.FAILED:
    print(f"Error: {result.error}")
    # Handle error (retry, notify user, etc.)

if result.status == PublishingStatus.PUBLISHED:
    print(f"Success! URL: {result.url}")
```

## Format Details

### HTML Export

Features:
- Professional styling with responsive design
- Self-contained (no external dependencies)
- Metadata and SEO information included
- Reading time calculation
- Mobile-friendly layout
- Print-friendly styling

Use cases:
- Sharing articles via email
- Publishing to personal website
- Archiving
- Creating standalone documents

### Markdown Export

Features:
- Preserves article structure
- Includes frontmatter with metadata
- Clean formatting
- Easy to edit further

Use cases:
- Integration with static site generators (Jekyll, Hugo)
- Version control and collaboration
- Migrating to other platforms
- Archive and backup

### JSON Export

Features:
- Complete pipeline output
- All stages of processing preserved
- Structured data for programmatic access
- Serializable and portable

Use cases:
- Data analysis and processing
- Integration with other systems
- API responses
- Archival with full context

### CSV Export

Features:
- Spreadsheet-compatible
- Organized by content type
- Includes metadata

Use cases:
- Data analysis in Excel/Sheets
- Creating reports
- Content analysis
- Bulk operations

## Extending the System

### Adding a New Publisher

```python
from youtube_to_article.publishers.base import (
    BasePublisher, PublishConfig, PublishingResult,
    PublishingStatus, PublishingPlatform
)

class DevToPublisher(BasePublisher):
    """Publish articles to Dev.to"""

    def __init__(self, api_token: str):
        super().__init__(api_token)
        self.platform = PublishingPlatform.DEVTO

    def publish(self, final_output, config):
        # Implementation
        return PublishingResult(...)

# Register and use
manager = PublishingManager()
publisher = DevToPublisher(token)
manager.register_publisher("devto", publisher)
result = manager.publish(final_output, "devto", config)
```

### Adding a New Export Format

```python
from youtube_to_article.exporters.base import BaseExporter

class PDFExporter(BaseExporter):
    """Export articles as PDF"""

    @property
    def file_extension(self):
        return "pdf"

    def export(self, final_output, filename=None):
        # Implementation
        return output_path

# Register in PublishingManager
manager.AVAILABLE_EXPORTERS["pdf"] = PDFExporter
```

## Troubleshooting

### Medium Publishing Issues

**"Failed to retrieve Medium user ID"**
- Verify your API token is correct
- Check token permissions in Medium settings
- Ensure token is not expired

**"HTTP 401: Unauthorized"**
- Invalid or expired API token
- Generate a new token from Medium settings

**"Invalid tag format"**
- Tags cannot contain special characters
- Maximum 5 tags per article
- Remove commas from tag names

### Export Issues

**"Permission denied" errors**
- Check output directory permissions
- Ensure write access to output directory
- Try using absolute paths

**"Invalid markdown" in HTML export**
- Verify the markdown library is installed
- Check for special characters in article content

## Performance Considerations

- **Large articles**: HTML export may take longer due to styling
- **API calls**: Medium publishing requires network connectivity
- **Concurrent publishing**: Publish to multiple platforms sequentially
- **File I/O**: Batch operations when possible

## Security

- **API Tokens**: Never commit tokens to version control
- **Canonical URLs**: Verify URLs before publishing
- **Draft mode**: Always review Medium drafts before publishing
- **History files**: Store history files securely with appropriate permissions

## Best Practices

1. **Always export first**: Keep backups in multiple formats
2. **Use draft mode**: Review drafts on platform before publishing live
3. **Set canonical URLs**: Help search engines find original content
4. **Use descriptive tags**: Improve discoverability of articles
5. **Monitor history**: Track publishing performance and issues
6. **Test configurations**: Test with draft mode before publishing live
7. **Batch operations**: Group similar operations for efficiency

## API Reference

### PublishingManager

```python
manager = PublishingManager(output_dir, history_dir)

# Export methods
exports = manager.export(final_output, formats, output_dir)
path = manager.export_single(final_output, format, output_dir)

# Publishing methods
result = manager.publish(final_output, platform, config)
results = manager.publish_to_multiple(final_output, platforms, config)
combined = manager.export_and_publish(...)

# History and stats
history = manager.get_publishing_history(video_id, article_slug)
stats = manager.get_statistics()
```

### Export Classes

- `MarkdownExporter`: Export to Markdown format
- `JSONExporter`: Export to JSON format
- `HTMLExporter`: Export to HTML format
- `CSVExporter`: Export to CSV format

### Publisher Classes

- `MediumPublisher`: Publish to Medium platform

## Examples

### Complete Workflow Example

```python
from pathlib import Path
from youtube_to_article.publishing import PublishingManager
from youtube_to_article.publishers.medium import MediumPublisher
from youtube_to_article.publishers.base import PublishConfig, PublishingPlatform

# Setup
output_dir = Path("./my_articles")
manager = PublishingManager(output_dir=output_dir)

# Export to multiple formats
exports = manager.export(
    final_output,
    formats=["markdown", "html", "json"]
)
print(f"Exported to: {exports}")

# Publish to Medium
medium = MediumPublisher(api_token="your_token")
manager.register_publisher("medium", medium)

config = PublishConfig(
    platform=PublishingPlatform.MEDIUM,
    draft=True,
    tags=["technology", "tutorial"],
    canonical_url=final_output.source_video.url
)

result = manager.publish(final_output, "medium", config)

if result.url:
    print(f"✅ Published! {result.url}")
    # Review on Medium before publishing live
else:
    print(f"❌ Error: {result.error}")
    # Handle error

# Check statistics
stats = manager.get_statistics()
print(f"Total articles published: {stats['total_publishes']}")
```

## Support

For issues or feature requests:
1. Check the troubleshooting section above
2. Review platform-specific documentation (Medium API docs)
3. Check logs for detailed error messages
4. Verify API credentials and permissions
