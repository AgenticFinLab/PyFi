import json
from pathlib import Path
from typing import Optional


def prompt_for_pdf_filter():
    return """
  You are an expert book classifier tasked with determining whether a given book title, presented in either English or Chinese, is likely to contain a substantial number of clear images, illustrations, charts, or diagrams. Your classification must be based solely on the title and informed by established domain knowledge about typical content formats across genres.

  Domain Knowledge Guidelines:

  Books LIKELY to contain lots of images/illustrations (KEEP):
    - Technical analysis books (技术分析)
    - Chart pattern books (形态学, 图表分析)
    - Trading strategy books (看盘, 趋势跟踪)
    - Candlestick/K-line analysis (k线, 蜡烛图)
    - Moving average analysis (均线)
    - Short-term trading (短线交易)
    - Elliott wave theory (艾略特波浪理论)
    - Chart pattern recognition (形态识别)
    - Technical indicators (技术指标)
    - Diagram-based analysis (图解分析)

  Books UNLIKELY to contain lots of images (DELETE):
    - Biographies/Memoirs (人物传记)
    - Personal finance theory (个人理财)
    - Business management (公司管理)
    - Forum discussions (论坛留言)
    - Entrepreneurship courses (创业教学)
    - Sales training (销售教学)
    - Historical economics (历史经济)
    - Theoretical finance (金融理论)
    - Philosophy books (哲学类)
    - Pure text-based analysis (纯文字分析)

  Classification Protocol:
    1. Examine the book title carefully, noting keywords, implied methodology, and subject domain.
    2. Assess whether the topic inherently relies on visual representation (e.g., charts, graphs, annotated diagrams).
    3. If the title clearly suggests a visually driven approach (e.g., "chart," "pattern," "illustrated," "K-line," "图解," "形态"), classify as KEEP.
    4. If the title indicates a theoretical, narrative, or text-based treatment (e.g., "theory," "principles," "history," "management," "传记," "哲学"), classify as DELETE.
    5. If the title is ambiguous or lacks sufficient contextual cues to determine visual density, classify as UNCERTAIN.

  Examples:
    - Technical Analysis of the Financial Markets return 'KEEP'  
    - 股票技术分析入门 return 'KEEP'  
    - The Intelligent Investor return 'DELETE'  
    - 巴菲特传记 return 'DELETE'  
    - Japanese Candlestick Charting Techniques return 'KEEP'  
    - k线/蜡烛图实战精髓 return 'KEEP'  
    - Principles of Corporate Finance return 'DELETE'  
    - 看盘技巧图解 return 'KEEP'  
    - Market Wizards: Interviews with Top Traders return 'DELETE'  
    - 艾略特波浪理论实战 return 'KEEP'  

  Output Requirement:  
  Respond with EXACTLY ONE WORD: 'KEEP', 'DELETE', or 'UNCERTAIN'
  """


def prompt_for_image_screener(contextual_information: Optional[str] = None) -> str:
    """Generates the prompt for image screening.

    Args:
        contextual_information: Optional string providing context for the image.

    Returns:
        A formatted string containing the full prompt.
    """
    base_prompt = """
    Core Task: Provide a set of basic requirements to determine whether the target image meets the criteria. 
    You need to evaluate and directly output the judgment result in standard JSON format.

    1. Background Information
    - The provided image may come from a financial platform, textbook, analytical report, news publication, or other sources.
    - Contextual information may be provided, which may or may not be directly related to the image. If relevant, it can be used as a reference for judgment:
    """
    context_part = (
        f"\n{contextual_information}\n" if contextual_information else "\nNone\n"
    )
    requirements_and_output = """

    2. Basic Requirements for the Target Image
    (1) The image must be a financial trend data chart exclusively, with no landscapes, people, logos, icons, covers, or non-informative elements (e.g., decorative graphics, abstract art, or irrelevant backgrounds). It must represent specific financial dynamics such as growth/decline trends, asset conversions, or capital circulations. 
    (2) The image must contain clearly legible Chinese characters or English words (e.g., axis labels, data points, or annotations), with no ambiguity in text recognition regardless of font size or color. If text is present, it must be human-readable without zooming or enhancement. 
    (3) The image must be free of obvious errors or omissions, including but not limited to: incorrect data scaling, missing timeframes, or inconsistent units. All visual elements must align with standard financial data practices. 
    (4) The image must prominently feature a visual representation of dynamic financial processes, such as: 
    - Trends (e.g., continuous line charts showing stock price growth/decline, commodity cycles), 
    - Conversions (e.g., flow diagrams of asset transformation or risk transfer), 
    - Circulations (e.g., heatmaps of capital flows between markets), 
    - Systemic transformations (e.g., before/after visuals of structural shifts in fintech). 
    (5) Any tabular or grid-like elements (e.g., cell borders, data tables) must serve only as secondary contextual overlays and cannot dominate the visual composition. Primary attention must be drawn to the dynamic process (e.g., curves or flows), not grids. 
    (6) The image must illustrate explicit relationships between elements through visual connections (e.g., arrows linking market phases, color-coded lines showing cause-effect interactions), reflecting simple or complex financial interdependencies. 
    (7) The image must reflect financial-related issues, specifically addressing at least one of: 
    - Price, volume, or volatility of financial assets (e.g., stocks, crypto, forex, real estate), 
    - Abstract financial analysis (e.g., risk modeling outputs), 
    - Structural changes in finance (e.g., sector evolution due to regulation), 
    - Cross-field impacts (e.g., how macroeconomic events affect asset prices). 
    (8) The image must be universally discernible under all conditions: 
    - Text and visuals must remain clear in grayscale or color, 
    - No dependency on high resolution (e.g., recognizable at standard screen sizes), 
    - Composition must be self-contained (single image or integrated multi-image charts without fragmented elements).

    3. Specific Task
    Determine whether the image meets the above requirements.

    4. Output Content
    Please evaluate the image against the basic requirements and assign a compliance score from 1 (non-compliant) to 10 (fully compliant).
    Also determine:
    - complexity_level: an integer from 1 to 10 indicating the visual complexity of the image.

    5. Strictly follow the JSON output format; no explanation is needed. Please return only pure JSON format, without any Markdown code block markers, explanatory text, or other formatting.
    For example:
    {
      "is_compliant": "yes/no",
      "compliance_level": 1-10,
      "complexity_level": 1-10
    }

    6. Examples
    If the image fully meets the requirements, output:
    {
      "is_compliant": "yes",
      "compliance_level": 10,
      "complexity_level": 8
    }
    If the image basicly meets the requirements, output:
    {
      "is_compliant": "yes",
      "compliance_level": 7,
      "complexity_level": 6
    }
    If the image does not meet the requirements at all, output:
    {
      "is_compliant": "no",
      "compliance_level": 1,
      "complexity_level": 3
    }
    """
    return base_prompt + context_part + requirements_and_output


def prompt_for_image_classification(root_dir: Path, book_id: str, image_id: str) -> str:
    """Builds the prompt with classification taxonomy and context information.

    Args:
        root_dir: Root directory containing context and image data.
        book_id: The ID of the book containing the image.
        image_id: The ID of the image to classify.

    Returns:
        The complete prompt including taxonomy and context information.
    """
    # Path to the context file containing metadata and surrounding text for the book
    context_file_path = root_dir / "context" / f"{book_id}.json"
    context_info = ""

    # Load context from JSON file if it exists
    if context_file_path.exists():
        try:
            # Open and parse the context JSON file
            with open(context_file_path, "r", encoding="utf-8") as f:
                context_data = json.load(f)

            image_context = None
            # Search for the specific image in the context data
            for item in context_data:
                # Check if the image filename matches the given image_id
                if item.get("image_filename", "").startswith(image_id):
                    image_context = item
                    break

            # Extract relevant context information based on classification type
            if image_context:
                # Get the classification type of the image
                classification = image_context.get("classification", "")

                # If it's a normal classification with caption references, use caption and reference text
                if classification == "normal" and image_context.get(
                    "caption_references"
                ):
                    # Get the nearest caption for the image
                    caption = image_context.get("nearest_caption", "")
                    # Get the list of caption references
                    references = image_context.get("caption_references", [])

                    # Process the first reference if it exists
                    if references and len(references) > 0:
                        ref_content = references[0]

                        # Check if there are actual references in the content
                        if ref_content.get("references"):
                            # Get the first reference detail
                            ref_detail = ref_content["references"][0]

                            # If it's an exact match, include the reference paragraph in context
                            if ref_detail.get("is_exact_match", False):
                                context_info = (
                                    f"Context Information:\n"
                                    f"Caption: {caption}\n"
                                    f"Reference Text: {ref_detail.get('reference_paragraph', '')}\n\n"
                                )
                else:
                    # For other classifications, use the surrounding text of the image
                    surround_text = image_context.get("image_surround_text", "")
                    context_info = (
                        f"Context Information:\n"
                        f"Surrounding Text: {surround_text}\n\n"
                    )
        except Exception as e:
            # Print error message if there's an issue reading the context file
            print(f"Error reading context file for {book_id}: {e}")

    # Construct the full prompt including taxonomy
    # Initial instruction for the AI model to act as a financial data analyst
    prompt = (
        "You are an expert financial data analyst specializing in economic and market "
        "visualization classification. Your task is to analyze the provided image and "
        "categorize it according to the specified taxonomy.\n\n"
    )

    # Add context information if available
    if context_info:
        prompt += context_info

    # Complete prompt with taxonomy and instructions
    prompt += """Please classify the image according to the following taxonomy:

      I. Content Theme
      1. Macroeconomic Indicators
      2. Financial Markets & Products
      3. Commodities & Real Estate Markets
      4. Bonds & Fixed Income
      5. Monetary & Fiscal Policy
      6. International Trade & Capital Flows
      7. Corporate Finance & Valuation
      8. Industry Analysis
      9. Investment Theory & Portfolio Management
      10. Risk Models & Management
      11. Economic Cycles & Market Theories
      12. Microeconomic Principles
      13. Demographics & Socioeconomics
      14. Financial Systems & Infrastructure
      15. Organization & Regulation
      16. Geospatial Economic Data
      17. Financial History & Documentation

      II. Chart Type / Format
      1. Line Chart
      2. Bar Chart / Column Chart
      3. Pie Chart / Donut Chart
      4. Scatter Plot / Bubble Chart
      5. Table
      6. Diagram / Schematic
      7. Radar Chart
      8. Heatmap
      9. Candlestick Chart / OHLC Chart
      10. Photograph
      11. Infographic

      Instructions:
      - Analyze the image carefully and identify ALL applicable categories
      - Consider the provided context information when making your classification
      - Return your answer in JSON format with two lists: "content_theme" and "chart_type", each containing the applicable IDs
      - If no categories apply, return empty lists
      - Be precise and only select categories that clearly match the image content

      Example response format: {"content_theme": [1, 5], "chart_type": [2, 11]}

      Provide only the JSON response, no additional text or explanations."""

    # Return the complete classification prompt
    return prompt


def prompt_for_ref_info_extraction(text_snippet: str) -> str:
    """Generates the default LLM prompt for reference information extraction.

    Returns:
        A formatted string containing the complete prompt for the LLM.
    """
    return f"""You are an expert bibliographic information extractor. 
Analyze the provided text snippet, which is the beginning and end of a Markdown document. 
Your task is to identify and extract key bibliographic details. 
Respond ONLY with a valid JSON object containing the fields listed below. 
If a field's value cannot be found, set its value to `null`. 
Do NOT include any explanations, markdown formatting (like ```json), or extra text.

Fields to extract:
- type (string): The type of the source. Must be one of 'book', 'report', or 'unknown'.
- authors (array of strings or null): A list of author names. Can be null if not found.
- year (string or null): The publication year (e.g., '2023').
- title (string or null): The full title of the book or report.
- edition (string or null): The edition of the book (e.g., '2nd ed.', '修订版').
- translators (array of strings or null): A list of translator names. Can be null if not found.
- publisher (string or null): The name of the publisher.
- isbn (string or null): The ISBN for books.
- report_number (string or null): The report number for technical reports.
- institution (string or null): The issuing institution for reports.
- location (string or null): The place of publication (e.g., 'Beijing').
- url (string or null): A URL where the source can be found.
- access_date (string or null): The date the source was accessed (e.g., '2024-05-21').
- category (string or null): The financial-related category of the source. Choose from: 
'Investment Decision', 'Corporate Management', 'Policy Making', 'Risk Management', 
'Market Research', 'Academic Research', 'Personal Finance', 'FinTech', 'Sustainability & ESG', 
'International Business'. Set to null if not determinable.

Example format:
{{
  "type": "book",
  "authors": ["John Doe"],
  "year": "2023",
  "title": "Introduction to Finance",
  "edition": null,
  "translators": null,
  "publisher": "Finance Press",
  "isbn": "978-1234567890",
  "report_number": null,
  "institution": null,
  "location": "New York",
  "url": null,
  "access_date": null,
  "category": "Investment Decision"
}}

Text to analyze:
{text_snippet}
"""


def prompt_for_context_summarization(text: str) -> str:
    """Create the prompt for the summarization task.

    Constructs a detailed prompt instructing the LLM to extract image background
    and analysis information from the provided text, following specific formatting
    and content requirements.

    Args:
        text: The text to be summarized.

    Returns:
        str: Formatted prompt for the LLM.
    """
    return f"""
    1. Core task
    Given a multi-paragraph content where the first two sentences refer to the target image, please directly extract the image background and the concise analysis information. 

    3. Requirements
    - The image background only contains the caption, general setting and subject. 
    - The image background must not contain any analytical statements, rankings, statistics, comparative descriptions, conclusions, results and subjective opinions. 
    - The image background must also extract all abbreviations and acronyms.
    - The analysis information consists of contextual, interpretive or evaluative insights regarding the image's meaning, significance, or implications.
    - Must be strictly in English.
    - Must spell out all abbreviations and acronyms.

    4. Output Format (JSON):
    {{
        "image_background": "your extracted image background here",
        "analysis_information": "your summarized analysis information here"
    }}

    5. Given Content:
    ########        
    {text}
    ########
    """
