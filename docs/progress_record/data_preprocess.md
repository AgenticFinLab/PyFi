## Data Preprocessing Pipeline Description

> This document provides a detailed overview of the data preprocessing pipeline employed in ***PyFi***. Designed to extract financial images and their associated metadata from raw financial documents, the pipeline supports the construction of a structured visual question answering (VQA) dataset, thereby enabling the training and evaluation of financial image understanding and reasoning models.

### Table of Contents   
1. [PDF Preparation](#1-PDF-Preparation): Collect raw financial PDF documents.
2. [PDF Filtering](#2-PDF-Filtering): PDF quality control and filtering.
3. [PDF Parsing](#3-PDF-Parsing): Extract text and images from PDFs.
4. [File Reorganization](#4-File-Reorganization): Reorganize parsed files into a structured directory.
5. [Image Screening](#5-Image-Screening): Filter out non-financial images.
6. [Context Extraction](#6-Context-Extraction): Extract financial context from text.
7. [Image Classification](#7-Image-Classification): Classify images into categories.
8. [Reference Info Extraction](#8-Reference-Info-Extraction): Extract reference information from text.
9. [Image Statistics](#9-Image-Statistics): Calculate statistics of the image dataset.
10. [Image Sampling](#10-Image-Sampling): Sample images for VQA dataset construction.
11. [Context Summarization](#11-Context-Summarization): Summarize the context for each remaining image.
12. [Abbreviation Expansion](#12-Abbreviation-Expansion): Expand abbreviations in text.
13. [Context Summarization via LLM](#13-Context-Summarization-via-LLM): Summarize the context using LLM.
14. [File Distribution](#14-File-Distribution): Distribute image-context pairs into a hierarchical directory structure.


---

### 1. PDF Preparation

The data processing pipeline begins with collecting a large corpus of raw PDF documents through web crawling methods or official database APIs. We provide representative sources in both Chinese and English, including Bank of China's macroeconomic research reports and relevant World Bank publications.

#### Basic Usage

```bash
# Download all PDFs to the raw_pdfs directory by default
python examples/data_preprocess/pdf_scraper.py

# Specify a custom output directory
python examples/data_preprocess/pdf_scraper.py --output_dir my_pdfs

# Crawl specific source (Bank of China only) and save to a specific directory
python examples/data_preprocess/pdf_scraper.py --sources boc --output_dir china_reports

# Crawl specific source (World Bank only) and specify a custom output directory and keywords
python examples/data_preprocess/pdf_scraper.py --sources worldbank --output_dir my_pdfs --keywords "finance"
```

#### Parameters

| Parameter      | Short Form | Default Value                                                                                         | Description                                          |
| -------------- | ---------- | ----------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| `--output_dir` | `-o`       | `raw_pdfs`                                                                                            | Directory to save PDF files                          |
| `--sources`    | `-s`       | `all`                                                                                                 | Data sources to crawl (`boc`, `worldbank`, or `all`) |
| `--keywords`   | `-k`       | `finance OR economics OR economic OR financial OR fiscal OR budget OR trade OR investment OR banking` | Keywords to filter World Bank reports                |

---

### 2. PDF Filtering

This filtering step does not precisely identify PDFs containing high-quality financial images suitable for our research. Instead, it performs two main functions:

1. **Technical filtering**: Removes corrupted, encrypted, or otherwise unreadable PDF files

2. **Domain relevance filtering**: Uses prior knowledge from manual review of thousands of PDFs to eliminate documents clearly outside our research scope, based on:
   - **Exclusion criteria**: Documents containing keywords like "biography", "personal finance", "company management", "forum posts", "entrepreneurship teaching", "sales training", or "historical economics" are typically irrelevant to our research
   - **Inclusion criteria**: Documents with titles containing keywords such as "technical analysis", "chart patterns", "market analysis", "trend", "K-line", "moving average", "short-term trading", or "Elliott wave theory" often contain valuable financial images and are preserved

#### Prerequisites

API Key Required - Before using this tool, you must configure your DashScope API key.
You can obtain the key from the [Bailian console](https://bailian.console.aliyun.com/#/home).

```bash
# Linux/macOS
export DASHSCOPE_API_KEY="your_api_key_here"

# Windows PowerShell
$env:DASHSCOPE_API_KEY="your_api_key_here"

# Windows Command Prompt
set DASHSCOPE_API_KEY=your_api_key_here
```

#### Basic Usage

```bash
# Filter PDFs with manual review (keeps all categorized files for inspection)
python examples/data_preprocess/pdf_filter.py --input_dir raw_pdfs

# Process PDFs from a custom directory with automatic cleanup
python examples/data_preprocess/pdf_filter.py --input_dir my_pdfs --auto_cleanup

# Use a custom minimum file size (e.g., 2MB instead of default 1MB)
python examples/data_preprocess/pdf_filter.py --input_dir raw_pdfs --size_threshold 2

```

#### Parameters

| Parameter             | Short Form | Default Value                                              | Description                                                                |
| --------------------- | ---------- | ---------------------------------------------------------- | -------------------------------------------------------------------------- |
| `--input_dir`             | `-i`       | `raw_pdfs`                                                 | Input directory containing PDF files to filter                             |
| `--auto_cleanup`      | `-c`       | `False`                                                    | Automatically delete files in `to_delete`/`uncertain` folders (without review) |
| `--size_threshold`    | `-s`       | `1` (1 MB)                                           | Minimum file size in bytes to retain during initial screening              |

The **prompt** used for filtering PDFs is defined in `fttracer/tools/data_preprocess/prompt.py`. You can modify this prompt to suit your specific needs. The default model is `qwen-plus`.

#### Output

The script will create three subdirectories within the specified `--input_dir`:

- `to_keep/`: Contains high-quality financial documents with valuable images
- `to_delete/`: Contains low-quality or irrelevant documents
- `uncertain/`: Contains documents that require manual review

> **Note**: The filtering process is designed as an initial screening step. The `uncertain/` folder contains documents that require manual verification to determine their suitability for the financial image understanding benchmark.

---

### 3. PDF Parsing

Utilize the powerful open-source PDF parser [Mineru's API](https://mineru.net/apiManage/docs) to process the validated PDF collection. The API Tokens provided by MinerU are valid for 14 days. Please renew the API Tokens before they expire.

> note: Since the MinerU API is currently in a trial/testing phase, parsing performance may be affected by factors such as network instability or API rate limiting. For more stable results, we recommend using a locally deployed version of [MinerU](https://github.com/opendatalab/mineru?tab=readme-ov-file).

#### Prerequisites

For security reasons, we recommend setting the API key via environment variable instead of command line:

```bash
# Linux/macOS
export MINERU_API_KEY="your_secure_api_key"

# Windows (PowerShell)
$env:MINERU_API_KEY="your_secure_api_key"
```

#### Basic Usage

```bash
# Parse PDFs with default settings
python examples/data_preprocess/pdf_parser.py

# Process PDFs with custom settings
python examples/data_preprocess/pdf_parser.py \
  --input_dir "financial_reports" \
  --output_dir "parsed_data" \
  --batch_size 100 \
  --language "zh"

# Process Chinese financial documents without size checking
python examples/data_preprocess/pdf_parser.py \
  --input_dir "china_reports" \
  --language "zh" \
  --no_check_pdf_limits

# Reorganize files in current working directory
python examples/data_preprocess/file_reorganizer.py \
  --input_dir "./" \
  --output_dir "./reorganized"
```

#### Parameters

| Parameter            | Short Form | Default Value            | Description                                                 |
| -------------------- | ---------- | ------------------------ | ----------------------------------------------------------- |
| `--input_dir`        | `-i`       | `raw_pdfs`               | Source directory containing PDF files                       |
| `--output_dir`       | `-o`       | `parse_results`          | Output directory for processed results                      |
| `--batch_size`       | `-b`       | `200`                    | Maximum number of files per processing batch                |
| `--language`         | `-l`       | `en`                     | Document language code                                      |
| `--no_check_pdf_limits` |            | `False`                   | Disable automatic validation and splitting of oversized PDFs |

**Note**: Mineru API has strict limitations - PDFs must be under **200MB** and **600 pages**. Each batch can process up to **200 PDF files**.
Files exceeding these limits will fail to process unless `check_pdf_limits` is enabled.

When `check_pdf_limits=True` (default):
- Automatically detects oversized PDFs
- Splits them into valid chunks (≤200MB, ≤600 pages)
- Processes each chunk through Mineru API
- Seamlessly merges results to maintain document integrity

---

### 4. File Reorganization

Reorganize the parsed results into a standardized directory structure optimized for subsequent processing stages. 

#### Basic Usage

```bash
# Reorganize files with default directories
python examples/data_preprocess/file_reorganizer.py

# Specify custom input and output directories
python examples/data_preprocess/file_reorganizer.py \
  --input_dir "parsed_documents" \
  --output_dir "standardized_repository"
```

#### Parameters

| Parameter      | Short Form | Default Value         | Description                                                      |
| -------------- | ---------- | --------------------- | ---------------------------------------------------------------- |
| `--input_dir`  | `-i`       | `parse_results`       | Source directory containing Markdown files and associated images |
| `--output_dir` | `-o`       | `reorganized_results` | Target directory for standardized output structure               |

#### Input/Output Structure

**Input Structure Example:**
```
input/
├── BookA/
│   ├── full.md
│   ├── images/
│   │   └── fig1.jpg
│   └── BookA.pdf
└── BookB/
    ├── full.md
    ├── images/
    │   └── fig2.jpg
    └── BookB.pdf
```

**Output Structure Example:**
```
output/
├── markdown/
│   ├── 000001.md
│   └── 000002.md
├── images/
│   ├── 000001/
│   │   └── 000001.jpg
│   └── 000002/
│       └── 000001.jpg
└── pdf/
    ├── 000001.pdf
    └── 000002.pdf
```

---

### 5. Image Screening

Conduct detailed review of each extracted image to quantitatively assess its compliance to the research and complexity level. After screening, manual review should be performed based on the generated JSON results.
Additionally, this step provides two versions of the code to accommodate different data scales. The synchronous `image_screener.py` is optimized for small-scale data processing using DashScope API. The asynchronous `image_screener_asyn.py` is designed for large-scale batch processing with ARK API. Choose the appropriate version based on your dataset size and processing requirements.

#### Prerequisites

##### For Small-Scale Data Processing
You need to configure your DashScope API key before using this tool:

```bash
# Linux/macOS
export DASHSCOPE_API_KEY="your_api_key_here"

# Windows PowerShell
$env:DASHSCOPE_API_KEY="your_api_key_here"

# Windows Command Prompt
set DASHSCOPE_API_KEY=your_api_key_here
```

##### For Large-Scale Batch Processing
For asynchronous batch inference, configure the following ARK API credentials:
You can obtain these credentials from [VolcEngine](https://www.volcengine.com/).

```bash
# Linux/macOS
export ARK_API_KEY="your_api_key_here"
export VOLC_ACCESSKEY="your_access_key_here"
export VOLC_SECRETKEY="your_secret_key_here"

# Windows PowerShell
$env:ARK_API_KEY="your_api_key_here"
$env:VOLC_ACCESSKEY="your_access_key_here"
$env:VOLC_SECRETKEY="your_secret_key_here"

# Windows Command Prompt
set ARK_API_KEY=your_api_key_here
set VOLC_ACCESSKEY=your_access_key_here
set VOLC_SECRETKEY=your_secret_key_here
```

After configuring your API key, you also need to set up an inference endpoint (endpoint_id). Please refer to the documentation: [docs](https://www.volcengine.com/docs/82379/1099522)


```python
import os
from volcenginesdkarkruntime import Ark
# Read your Ark API Key from environment variables
client = Ark(api_key=os.environ.get("<YOUR_API_KEY>"))
completion = client.chat.completions.create(
    # Replace <Model> with your Endpoint ID
    model="<Model>", 
    messages=[
        {"role": "user", "content": "Hello"}
    ]
)
print(completion.choices[0].message)
```

#### Basic Usage

```bash
# Screen images using default input directory (reorganized_results)
python examples/data_preprocess/image_screener.py

# Specify custom input directory
python examples/data_preprocess/image_screener.py --input_dir my_reorganized_data

# Process with larger batches (5 images per request)
python examples/data_preprocess/image_screener_asyn.py --batch_size 5

# Increase concurrency for faster processing (10 workers)
python examples/data_preprocess/image_screener_asyn.py --worker_count 10

# Full custom configuration
python examples/data_preprocess/image_screener_asyn.py --input_dir my_reorganized_data --batch_size 4 --worker_count 8
```

#### Parameters

| Parameter        | Short Form | Default Value         | Description                                                 |
| ---------------- | ---------- | --------------------- | ----------------------------------------------------------- |
| `--input_dir`    | `-i`       | `reorganized_results` | Directory containing reorganized image files to be screened |
| `--batch_size`   | `-b`       | `1`                   | Number of images to process per batch (only for asynchronous batch inference)                      |
| `--worker_count` | `-w`       | `5`                   | Number of concurrent workers for parallel processing (only for asynchronous batch inference)         |

The **prompt** used for screening images is defined in `fttracer/tools/data_preprocess/prompt.py`. You can modify this prompt to suit your specific needs. The default model is `doubao-seed-1-6-flash`.

#### Output Format

The tool generates structured JSON files in the `context` subdirectory:

```
<input_dir>/images_eval/
  ├── 000001/
  │ ├── 000001.json
  │ └── 000002.json
  └── 000002/
    ├── 000001.json
    └── 000002.json
```

Example JSON output:

```json
{
  "is_compliant": "yes",
  "compliance_level": 7,
  "complexity_level": 6
}
```

Where:
- `is_compliant`: "yes" or "no" indicating if the image meets quality standards
- `compliance_level`: Numerical score (1-10) representing quality compliance
- `complexity_level`: Numerical score (1-10) indicating image complexity

---

### 6. Context Extraction

This module processes book reports to extract image-related context from Markdown files, analyze image classifications (normal, abnormal, extreme abnormal), and generate structured JSON outputs for downstream tasks.

>**NOTE**: For the detailed pipeline, classification rules, and examples, see: [image_context_extraction.md](image_context_extraction.md)

#### Basic Usage

```bash
# Extract context using default input directory (reorganized_results)
python examples/data_preprocess/context_extractor.py

# Specify custom input directory
python examples/data_preprocess/context_extractor.py --input_dir my_reorganized_data
```

#### Parameters

| Parameter     | Short Form | Default Value         | Description                                              |
| ------------- | ---------- | --------------------- | -------------------------------------------------------- |
| `--input_dir` | `-i`       | `reorganized_results` | Directory containing the reorganized financial documents |

#### Input Directory Structure

The tool expects the following directory structure reorganized in [Section 4](#4-file-reorganization):

```
<input_dir>/
├── markdown/
│   ├── 000001.md
│   └── 000002.md
├── images/
│   ├── 000001/
│   │   └── 000001.jpg
│   └── 000002/
│       └── 000001.jpg
└── pdf/
    ├── 000001.pdf
    └── 000002.pdf
```

#### Output

The tool generates structured JSON files in the `context` subdirectory:

```
<input_dir>/context/
    ├── 000001.json
    └── 000002.json
```

---

### 7. Image Classification

In this study, the images are classified into 17 financial content themes and 11 chart types using a Vision Language Model (VLM). The specific classification categories are defined in [image category doc](../../docs/progress_record/image_category.md).

#### Prerequisites

The API key configuration and inference endpoint configuration here are the same as those in Section 5. Please refer to the "For Large-Scale Batch Processing" configuration in [Image Screening](#5-Image-Screening).

####  Basic Usage

```bash
# Run classification with default parameters
python examples/data_preprocess/image_classifier.py

# Customize batch size and worker count
python examples/data_preprocess/image_classifier.py --batch_size 2 --worker_count 8

# Process images with larger batches for better throughput
python examples/data_preprocess/image_classifier.py --input_dir my_data --batch_size 4 --worker_count 10

# Conservative processing with minimal resource usage
python examples/data_preprocess/image_classifier.py --batch_size 1 --worker_count 2
```

#### Parameters

| Parameter        | Short Form | Default Value         | Description                                              |
| ---------------- | ---------- | --------------------- | -------------------------------------------------------- |
| `--input_dir`    | `-i`       | `reorganized_results` | Root directory containing 'images' and 'context' folders |
| `--batch_size`   | `-b`       | `1`                   | Number of images to process in each batch                |
| `--worker_count` | `-w`       | `5`                   | Number of concurrent workers for parallel processing     |

The **prompt** used for image classification is defined in `fttracer/tools/data_preprocess/prompt.py`. You can modify this prompt to suit your specific needs. The default model is `doubao-seed-1-6-flash`.

#### Performance Considerations

- **Higher batch size** improves throughput but requires more memory
- **More workers** increases parallelism but may hit API rate limits
- Optimal settings depend on your hardware capabilities and API provider limitations

#### Output

The tool generates structured JSON files in the `image_classification` subdirectory:

```
<input_dir>/image_classification/
  ├── 000001/
  │ ├── 000001.json
  │ └── 000002.json
  └── 000002/
    ├── 000001.json
    └── 000002.json
```
Example JSON contains the following fields:

```json
{
  "content_theme": [
    1,
    13
  ],
  "chart_type": [
    10
  ]
}
```


---

### 8. Reference Info Extraction

Extract bibliographic reference and citation information from the processed PDF documents using advanced language model capabilities.

#### Prerequisites

The API key configuration here are the same as those in Section 5. Please refer to the [Image Screening](#5-Image-Screening).

#### Basic Usage

```bash
# Extract reference information using default input directory
python examples/data_preprocess/ref_info_extractor.py

# Specify custom input directory
python examples/data_preprocess/ref_info_extractor.py --input_dir my_reorganized_data
```

#### Parameters

| Parameter     | Short Form | Default Value         | Description                                              |
| ------------- | ---------- | --------------------- | -------------------------------------------------------- |
| `--input_dir` | `-i`       | `reorganized_results` | Directory containing the reorganized financial documents |

The **prompt** used for reference info extraction is defined in `fttracer/tools/data_preprocess/prompt.py`. You can modify this prompt to suit your specific needs. The default model is `doubao-1-5-pro-32k-250115`.

#### Output

The tool generates structured JSON files in the `reference_info` subdirectory:

```
<input_dir>/reference_info/
    ├── 000001.json
    └── 000002.json
```

---

### 9. Image Statistics

After image classification, we calculate the statistics of the image dataset. The statistics include the number of images per complexity level, compliance level, content theme, and chart type.

#### Basic Usage

```bash
# Analyze statistics using default directory
python examples/data_preprocess/image_statistics.py

# Specify custom directory
python examples/data_preprocess/image_statistics.py --base_dir my_data_dir --output_file my_statistics.txt
```

#### Parameters

| Parameter      | Short Form | Default Value               | Description                                              |
| -------------- | ---------- | --------------------------- | -------------------------------------------------------- |
| `--base_dir`   | `-i`       | `PyFi`                      | Directory containing the image classification and evaluation JSON files |
| `--output_file`| `-o`       | `image_statistics_summary.txt` | Output file to save the generated statistics summary     |

#### Output

The tool generates a plain-text summary file (`image_statistics_summary.txt` by default) containing:

- Distribution of compliance levels (counts and percentages)
- Distribution of complexity scores
- Breakdown of chart type frequencies
- Distribution of content themes
- Total number of processed images and JSON files
- Basic descriptive statistics (mean, median, min, max, etc.) where applicable

Example output snippet:
```
=== Compliance Level Distribution ===
Level 10: 12,345 (61.7%)
Level 9:  7,655 (38.3%)
Total:    20,000

=== Chart Type Distribution ===
Type 1 (Bar Chart):       5,200
Type 2 (Line Chart):      4,800
Type 6 (Table):           3,900
...
```

---

### 10. Image Sampling

We sample the images based on the statistics calculated in [Image Statistics](#9-Image-Statistics). For the detailed sampling strategy, refer to [Image Sampling Doc](image_sampling.md).

#### Basic Usage
```bash
# Sample images using default parameters
python examples/data_preprocess/image_sampler.py

# Specify custom base directory
python examples/data_preprocess/image_sampler.py --base_dir my_data_dir

# Sample with custom parameters
python examples/data_preprocess/image_sampler.py \
    --base_dir PyFi \
    --compliance_thresholds 9 10 \
    --complexity_top_n 20000 \
    --output_filename sampled_images_indices.txt \
    --filtered_output_filename sampled_images_indices_filtered.txt \
    --keep_chart_types 1 2 6 9 11 \
    --sampling_limit_per_theme 200
```

#### Parameters
| Parameter | Short Form | Default Value | Description |
| --------- | ---------- | ------------- | ----------- |
| `--base_dir` | `-b` | `PyFi` | Base directory path where evaluation and classification JSON files are stored |
| `--compliance_thresholds` | `-c` | `[9, 10]` | List of compliance levels to filter by (images must have compliance level in this list) |
| `--complexity_top_n` | `-n` | `20000` | Number of top complex images to extract after compliance filtering |
| `--output_filename` | `-o` | `sampled_images_indices.txt` | Output file to save sampled image indices **before** chart/theme filtering |
| `--filtered_output_filename` | `-f` | `sampled_images_indices_filtered.txt` | Output file to save indices **after** filtering by chart types and content themes |
| `--keep_chart_types` | `-k` | `[1, 2, 6, 9, 11]` | List of chart type IDs to retain (others are excluded) |
| `--sampling_limit_per_theme` | `-s` | `200` | Maximum number of images to keep per content theme (to ensure balance) |
| `--show_stats` | `-v` | `False` | Whether to print detailed statistics about compliance and complexity distributions |

> **Note**: The script produces **two output files**:  
> - One with raw top-complexity samples (`-o`)  
> - One further filtered by chart type and per-theme limits (`-f`)

#### Output Format
Both output files contain image indices in the format `book_id-image_id` (e.g., `000001-000045`), where:
- `book_id`: Zero-padded directory identifier (6 digits)
- `image_id`: Zero-padded file identifier without extension (6 digits)

> **Note**: After obtaining the filtered image indices, we copy the selected images and related files to a new directory automatically. The new directory will be named **`<base_dir>_selected`**.

#### Statistics Output
When `--show_stats` (or `-v`) is enabled, the script displays comprehensive statistics including:
- Total count, mean, median, min, max, and standard deviation for both compliance and complexity levels
- Distribution percentages for each discrete level value
- Total number of processed JSON files
- Breakdown of chart type and content theme distributions (if filtering is applied)

---

### 11. Context Summarization

In [Section 6](#6-context-extraction), the extracted context, being in JSON format and containing substantial content, could overwhelm the model if directly inserted into the prompt during subsequent question-answer pair generation. Therefore, we summarize this context in this section.

> **Note**: At this stage, the sampled data folder contains seven subdirectories: `context/`, `image_classification/`, `images/`, `images_eval/`, `markdown/`, `pdf/`, and `reference_info/`.
>
> As introduced earlier, the source directory is renamed from `xxx_selected` to **`PyFi`** for brevity and consistency.

#### Basic Usage
```bash
# Summarize context using default input directory
python examples/data_preprocess/context_summarizer.py

# Specify custom input directory
python examples/data_preprocess/context_summarizer.py --input_dir my_reorganized_data
```

#### Parameters
| Parameter     | Short Form | Default Value | Description                                              |
| ------------- | ---------- | ------------- | -------------------------------------------------------- |
| `--input_dir` | `-i`       | `PyFi`        | Directory containing the reorganized financial documents |


#### Output
The tool generates structured JSON files in the `context_summary` subdirectory:
```
<input_dir>/context_summary/
  ├── 000001/
  │ ├── 000001.json
  │ └── 000002.json
  └── 000002/
    ├── 000001.json
    └── 000002.json
```

---

### 12. Abbreviation Expansion

Expands abbreviations appearing in both textual contexts and figures to ensure downstream models have access to complete, unambiguous information.

#### Workflow Overview
1. **Build an abbreviation–full form mapping table** from all Markdown documents. This table captures every potential abbreviation and its corresponding expansion.
2. **Extract abbreviations from images** (e.g., figures, charts) using VLMs, as visual content may contain critical domain-specific acronyms not present in text.
3. **Expand image-derived abbreviations** by matching them against the mapping table built in Step 1.
4. **Expand abbreviations in textual context summaries** by replacing each abbreviation’s first occurrence with its full form (e.g., “ROE (Return on Equity)”).
5. **Merge expanded image abbreviations into the processed context summaries**, enriching the context with visual-domain terminology.

#### Prerequisites

- Input directory must contain three subdirectories:
  - `markdown/`: Financial reports or documents in Markdown format.
  - `images/`: Corresponding figures in `.jpg` format (other formats configurable via code).
  - `context_summary/`: Contextual summaries in JSON format (output of [Section 11](#11-context-summarization)).

#### Basic Usage
```bash
# Use default input directory
python examples/data_preprocess/abbreviation_expander.py

# Specify custom paths
python examples/data_preprocess/abbreviation_expander.py \
    --input_dir my_data \
```

#### Parameters
| Parameter     | Short Form | Default Value | Description                                                     |
| ------------- | ---------- | ------------- | --------------------------------------------------------------- |
| `--input_dir` | `-i`       | `PyFi`        | Root directory containing `markdown/`, `images/`, and `context_summary/` subfolders. |

The **prompt** used for filtering PDFs is defined in `fttracer/tools/data_preprocess/prompt.py`. You can modify this prompt to suit your specific needs. The default model is `qwen3-max-preview`.

#### Output Structure
The pipeline generates the following subdirectories under `--input_dir`:
```
<input_dir>/
├── abbreviations_table/          # JSON files mapping abbreviations to full forms
├── image_acronyms/               # Raw abbreviations extracted from images
├── image_acronyms_expansion/     # Image abbreviations expanded using the mapping table
├── context_summary/              # (Input) Original context summaries (must exist beforehand)
├── context_summary_processed/    # Context summaries with text-based abbreviations expanded
└── context_summary_expanded/     # Final context summaries enriched with both text and image expansions
```

--- 

### 13. Context Summarization via LLM

In [Section 11](#11-context-summarization), the first-level summarization was performed to condense the contextual information. However, for more precise control over the content structure and to specifically separate image background from analytical insights, a second-level summarization is performed using a large language model in this section.

This second summarization step ensures:
- **Image Background**: Contains only factual information (caption, setting, subject) without analysis or opinions
- **Analysis Information**: Contains only interpretive or evaluative insights

#### Basic Usage
```bash
# Summarize context using default input and output directories
python examples/data_preprocess/context_summarizer_via_LLM.py

# Specify custom input and output directories
python examples/data_preprocess/context_summarizer_via_LLM.py --input_dir my_context_data
```

#### Parameters
| Parameter     | Short Form | Default Value         | Description                                              |
| ------------- | ---------- | --------------------- | -------------------------------------------------------- |
| `--input_dir` | `-i`       | `PyFi` | Source directory containing JSON files of contextual information|

> Note: The input directory must contain the `context_summary_expanded` subdirectory, which is the output of [Section 12](#12-abbreviation-expansion).

#### Output
The tool generates structured JSON files in the specified output directory, maintaining the same subdirectory structure as the input:
```
<output_dir>/context_summary_LLM/
  ├── 000001/
  │ ├── 000001.json
  │ └── 000002.json
  └── 000002/
    ├── 000001.json
    └── 000002.json
```

Each output JSON file contains the strictly separated contextual information in the format:
```json
{
  "image_background": "factual image background information without analysis",
  "analysis_information": "interpretive analysis about image meaning and significance"
}
```

---

### 14. File Distribution

After context summarization (see [Section 13](#13-Context-Summarization-via-LLM)), image-context pairs are ready to be organized into a scalable, hierarchical directory structure. This step is used to support distributed processing across multiple servers or workers.

> **Note**: The input directory is expected to contain two subdirectories:  
> - `images/`: storing image files
> - `context_summary_LLM/`: storing corresponding JSON context summaries


#### Basic Usage
```bash
# Distribute files using default settings
python examples/data_preprocess/file_distributor.py

# Customize the distribution structure
python examples/data_preprocess/file_distributor.py \
  --input_dir my_data \
  --num_servers 10 \
  --num_shells_per_server 50 \
  --image_extension .png
```

#### Parameters
| Parameter                   | Short Form | Default Value | Description                                                                 |
| --------------------------- | ---------- | ------------- | --------------------------------------------------------------------------- |
| `--input_dir`               | `-i`       | `PyFi`        | Source directory containing `images/` and `context_summary_LLM/`             |
| `--num_servers`             | `-s`       | `25`          | Number of top-level `data_server_XXX` directories to create                 |
| `--num_shells_per_server`   | `-sh`      | `20`          | Number of `data_shell_XXX` subdirectories within each server                |
| `--image_extension`         | `-ext`     | `.jpg`        | File extension used to identify image files (e.g., `.jpg`, `.png`, `.jpeg`) |

#### Output Structure
The utility populates a new subdirectory `data_folder/` inside the input directory with the following layout:
```
<input_dir>/data_folder/
  ├── data_server_001/
  │   ├── data_shell_001/
  │   │   ├── images/
  │   │   │   └── folder1/
  │   │   │       └── image1.jpg
  │   │   └── context/
  │   │       └── folder1/
  │   │           └── image1.json
  │   └── data_shell_002/
  │       ├── images/
  │       │   └── folder2/
  │       │       └── image3.jpg
  │       └── context/
  │           └── folder2/
  │               └── image3.json
  ├── data_server_002/
  │   └── ...
  └── ...
```
