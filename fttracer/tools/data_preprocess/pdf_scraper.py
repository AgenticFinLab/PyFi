"""
# Downloads PDFs from two reference sources:
# 1. Bank of China Macroeconomic Research Reports
# 2. World Bank Reports
"""

import os
import re
import time
from urllib.parse import urljoin
from typing import Any, Dict, List, Tuple, Union

import requests
from tqdm import tqdm
from bs4 import BeautifulSoup


def crawl_boc(
    output_dir: str = "boc_reports",
    max_pages: int = 26,
) -> None:
    """
    Crawls macroeconomic research reports from the Bank of China website.

    This function iterates through a specified number of pages on the BOC
    summary page, extracts links to report detail pages, visits each detail
    page to find PDF download links, and downloads the PDFs.

    Args:
        output_dir (str): The directory to save the downloaded PDF files.
                          Defaults to 'boc_reports'.
        max_pages (int): The maximum number of pages to crawl.
                         Defaults to 26.
    """
    # Base configuration constants for the Bank of China website structure
    base_url = "https://www.boc.cn/fimarkets/summarize/"
    pdf_base_url = "https://pic.bankofchina.com/bocappd/rareport/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    # Ensure the output directory exists, create it if it doesn't
    os.makedirs(output_dir, exist_ok=True)

    def get_page_content(url: str) -> str:
        """
        Fetches the raw HTML content of a given URL.

        Args:
            url (str): The URL to fetch.

        Returns:
            str: The HTML content as a string, or None if an error occurs.
        """
        try:
            # Send a GET request to the URL with headers and a timeout
            response = requests.get(url, headers=headers, timeout=10)
            # Explicitly set the encoding to UTF-8 to handle text correctly
            response.encoding = "utf-8"
            return response.text
        except Exception as e:
            # Log the error if needed, currently just return None
            print(f"Error fetching {url}: {e}")
            return None

    def parse_report_list(html: str) -> List[Tuple[str, str]]:
        """
        Parses the HTML of a list page to extract report titles and URLs.

        This function uses BeautifulSoup to find list items containing links
        to report detail pages. It filters these links based on expected
        URL prefixes.

        Args:
            html (str): The raw HTML string of the page.

        Returns:
            List[Tuple[str, str]]: A list of tuples containing (title, absolute_URL).
        """
        soup = BeautifulSoup(html, "html.parser")
        reports = []
        # Select all <li> elements within the <ul class="list"> container
        for item in soup.select("ul.list > li"):
            link = item.select_one("a")  # Find the first <a> tag inside the <li>
            if link:
                title = link.get_text(strip=True)  # Extract the link text as title
                href = link.get("href")  # Get the relative or absolute href
                if href:
                    # Define expected URL prefixes for valid report links
                    year_range = range(2008, 2026)
                    prefixes = ["/aboutboc/bi1/"] + [f"./{year}" for year in year_range]
                    # Check if the href starts with one of the expected prefixes
                    if any(href.startswith(p) for p in prefixes):
                        # Convert relative href to absolute URL using the base_url
                        report_url = urljoin(base_url, href)
                        reports.append((title, report_url))
        return reports

    def get_pdf_links(report_html: str) -> List[Tuple[Any, Union[str, Any]]]:
        """
        Parses the HTML of a report detail page to extract PDF download links.

        This function searches for anchor tags with href attributes ending in '.pdf'.

        Args:
            report_html (str): The raw HTML string of the report detail page.

        Returns:
            List[Tuple[Any, Union[str, Any]]]: A list of tuples containing
                                               (pdf_title, pdf_url).
        """
        soup = BeautifulSoup(report_html, "html.parser")
        pdf_links = []
        # Select all <a> tags within <li> tags that have an 'href' attribute
        for item in soup.select("li > a[href]"):
            href = item.get("href")
            # Check if the href ends with '.pdf' (case-insensitive)
            if href and href.lower().endswith(".pdf"):
                pdf_title = item.get_text(strip=True)  # Get the link text as title
                if href.startswith("http"):
                    # If href is already an absolute URL, use it directly
                    pdf_url = href
                else:
                    # Otherwise, join it with the pdf_base_url to form an absolute URL
                    pdf_url = urljoin(pdf_base_url, href)
                pdf_links.append((pdf_title, pdf_url))
        return pdf_links

    def download_pdf(pdf_title: str, pdf_url: str) -> None:
        """
        Downloads a PDF file from a given URL and saves it locally.

        This function sanitizes the title for filesystem compatibility,
        checks if the file already exists, and performs the download if necessary.

        Args:
            pdf_title (str): The title to use for the saved file.
            pdf_url (str): The URL of the PDF file to download.
        """
        # Sanitize the title to remove invalid characters for filenames
        safe_title = re.sub(r'[\\/*?:"<>|]', "", pdf_title)
        # Construct the full file path
        file_path = os.path.join(
            output_dir, f"{safe_title}"
        )  # Added .pdf extension for clarity

        # Skip download if the file already exists locally
        if os.path.exists(file_path):
            print(f"File already exists, skipping: {file_path}")
            return

        try:
            # Send a GET request to download the PDF content
            response = requests.get(pdf_url, headers=headers, timeout=10)
            if response.status_code == 200:
                # Write the binary content to the local file
                with open(file_path, "wb") as f:
                    f.write(response.content)
                # print(f"Downloaded: {file_path}")
            else:
                print(
                    f"Failed to download {pdf_url}, status code: {response.status_code}"
                )
        except Exception as e:
            # Log the error if the download fails
            print(f"Error downloading {pdf_url}: {e}")

    # --- Main Crawling Logic with Progress Bar ---
    # Use tqdm to create a progress bar for the pages being crawled
    for page_num in tqdm(range(max_pages), desc="Crawling BOC Pages"):
        # Construct the URL for the current page (first page is base_url, others are index_N.html)
        page_url = base_url if page_num == 0 else f"{base_url}index_{page_num}.html"
        html = get_page_content(page_url)
        if not html:
            print(f"Failed to get content for page {page_num}, skipping.")
            continue  # Move to the next page if fetching fails

        reports = parse_report_list(html)
        # Update progress bar description to show reports found on the current page
        pbar_reports = tqdm(
            reports, desc=f"Processing reports on page {page_num}", leave=False
        )
        for title, report_url in pbar_reports:
            pbar_reports.set_postfix_str(f"Fetching {title}")
            report_html = get_page_content(report_url)
            if not report_html:
                print(f"Failed to get content for report {title}, skipping.")
                continue  # Move to the next report if fetching fails

            pdf_links = get_pdf_links(report_html)
            # Update progress bar description for PDF downloads within the report
            pbar_pdfs = tqdm(
                pdf_links, desc=f"Downloading PDFs for '{title[:20]}...'", leave=False
            )
            for pdf_title, pdf_url in pbar_pdfs:
                pbar_pdfs.set_postfix_str(f"Downloading...")
                download_pdf(pdf_title, pdf_url)
                time.sleep(1)  # Respectful crawling delay between PDF downloads
        time.sleep(3)  # Delay between processing pages to be respectful to the server

    print("Finished crawling Bank of China reports.")


def crawl_worldbank(
    output_dir: str = "worldbank_reports",
    keywords: str = "finance OR economics OR economic OR financial OR "
    "fiscal OR budget OR trade OR investment OR banking",
) -> None:
    """
    Downloads World Bank reports using their public API.

    This function queries the World Bank Document & Reports API based on
    specified keywords and document type, then downloads the associated PDFs.

    Args:
        output_dir (str): The directory to save the downloaded PDF files.
                          Defaults to 'worldbank_reports'.
        keywords (str): Search terms for filtering reports. Defaults to common
                        financial/economic terms.
    """
    # API endpoint and default parameters for the World Bank API
    BASE_URL = "https://search.worldbank.org/api/v3/wds"
    PARAMS = {
        "format": "json",  # Request JSON response format
        "qterm": keywords,  # Search query terms
        "docty_exact": "Report",  # Filter for documents of type 'Report'
        "fl": "display_title,pdfurl,guid",  # Fields to return in the response
        "rows": 100,  # Number of records per page
    }

    # Ensure the output directory exists, create it if it doesn't
    os.makedirs(output_dir, exist_ok=True)

    def sanitize_filename(title: str) -> str:
        """
        Cleans a string to make it a safe filename by removing invalid characters.

        Args:
            title (str): The original title string.

        Returns:
            str: A sanitized version suitable for a filename.
        """
        # Replace characters that are invalid in filenames with an underscore
        return "".join(
            c if c.isalnum() or c in (" ", "-", "_") else "_" for c in title
        ).strip()

    def fetch_total_count() -> int:
        """
        Fetches the total number of reports matching the API query.

        This is done by making a query with 'rows' set to 0.

        Returns:
            int: The total count of matching documents, or 0 if an error occurs.
        """
        try:
            # Make a request to get only the total count, not the data
            res = requests.get(
                BASE_URL,
                params={**PARAMS, "rows": 0},  # Override rows to 0 for count only
            )
            res.raise_for_status()  # Raise an exception for bad status codes
            data = res.json()
            return data.get("total", 0)
        except Exception as e:
            print(f"Error fetching total count from World Bank API: {e}")
            return 0

    def fetch_page(offset: int) -> List[Dict[str, str]]:
        """
        Fetches a single page of report data from the API.

        Args:
            offset (int): The starting index for the records to fetch.

        Returns:
            List[Dict[str, str]]: A list of document data dictionaries.
        """
        try:
            res = requests.get(
                BASE_URL,
                params={**PARAMS, "os": offset},  # Add offset parameter
            )
            res.raise_for_status()
            data = res.json()
            # The documents are nested under the 'documents' key
            return data.get("documents", {})
        except Exception as e:
            print(f"Error fetching page with offset {offset} from World Bank API: {e}")
            return {}

    def download_pdf(title: str, url: str, guid: str) -> None:
        """
        Downloads and saves a PDF file from a given URL.

        Args:
            title (str): The display title of the report.
            url (str): The direct URL to the PDF file.
            guid (str): A unique identifier for the report.
        """
        if not url:
            print(f"No PDF URL found for title: {title}")
            return

        # Create a safe filename using the sanitized title and the GUID
        filename = f"{sanitize_filename(title)}_{guid}.pdf"
        filepath = os.path.join(output_dir, filename)

        # Skip download if the file already exists locally
        if os.path.exists(filepath):
            print(f"File already exists, skipping: {filepath}")
            return

        try:
            # Send a GET request to download the PDF content with a longer timeout
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()  # Raise an exception for bad status codes
            # Write the binary content to the local file
            with open(filepath, "wb") as f:
                f.write(resp.content)
            print(f"Downloaded: {filepath}")
        except Exception as e:
            # Log the error if the download fails
            print(f"Error downloading {url}: {e}")

    # --- Main Crawling Logic for World Bank ---
    total_reports = fetch_total_count()
    print(f"Found {total_reports} reports to download from the World Bank API.")

    if total_reports == 0:
        print("No reports found matching the criteria.")
        return

    # Use tqdm to create a progress bar for the total number of reports
    pbar = tqdm(total=total_reports, desc="Downloading World Bank reports")
    for offset in range(0, total_reports, PARAMS["rows"]):
        documents = fetch_page(offset)
        for doc_id, doc in documents.items():
            title = doc.get("display_title", "untitled")
            pdf_url = doc.get("pdfurl")
            guid = doc.get("guid", "unknown")
            if pdf_url:
                download_pdf(title, pdf_url, guid)
                pbar.update(1)  # Update the progress bar for each successful download
        time.sleep(0.5)  # Delay between API requests to be respectful
    pbar.close()  # Close the progress bar when finished

    print("Finished downloading World Bank reports.")


if __name__ == "__main__":
    # Example usage:
    # Crawl Bank of China reports
    crawl_boc(output_dir="china_bank_reports")
    # Crawl World Bank reports
    crawl_worldbank(
        output_dir="world_bank_reports",
        keywords="finance OR economics OR economic OR financial OR fiscal OR budget OR trade OR investment OR banking",
    )
