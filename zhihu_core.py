import os
import requests
import re
import json
import base64
import shutil
import io
import zipfile
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from urllib.parse import urlparse, unquote
from utils.font_decoder import ZhihuFontDecoder

# Ensure utils package structure if we are importing from it
# For now, I'll inline the font decoder logic or expect it to be in the same dir if I don't create a package.
# But `from utils.font_decoder` implies I need to create that structure.
# I will create a `utils` folder and put `font_decoder.py` there as well.

class ZhihuDownloader:
    def __init__(self, cookie=None):
        self.headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        if cookie:
            self.headers['Cookie'] = cookie
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.font_decoder = ZhihuFontDecoder()

    def download(self, url):
        """
        Main entry point. Downloads the URL, processes it, and returns the result as a zip file in bytes.
        """
        # 1. Fetch content
        try:
            response = self.session.get(url)
            response.raise_for_status()
        except Exception as e:
            raise Exception(f"Failed to fetch URL: {str(e)}")

        html_content = response.text
        soup = BeautifulSoup(response.content, "html.parser")
        
        # 2. Extract Title
        title = "Untitled"
        title_tag = soup.select_one("h1.Post-Title") or soup.select_one("h1.QuestionHeader-title")
        if title_tag:
            title = title_tag.get_text(strip=True)
            
        # Clean title for filename
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)

        # 3. Extract Content
        content_element = soup.select_one("div.Post-RichTextContainer") or soup.select_one("div.RichContent-inner")
        if not content_element:
            raise Exception("Could not find content element. URL might be invalid or paywalled (check cookies).")
            
        # 4. Handle Fonts (De-obfuscation)
        # Extract font data from HTML
        font_data = self._extract_font_data(html_content)
        if font_data:
            # We only use the first valid one or all? The original code logic was specific.
            # Let's try to load all found fonts.
            for font_item in font_data:
                try:
                    self.font_decoder.load_font(font_item)
                except:
                    pass
        
        # 5. Process Content (Images, formatting)
        # Create a temporary directory structure for the zip
        # Root/
        #   Title.md
        #   assets/
        #     img1.jpg
        
        mem_zip = io.BytesIO()
        
        with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            
            # Process Images
            downloaded_images = {}
            for img in content_element.find_all("img"):
                src = img.get('data-original') or img.get('src')
                if not src or src.startswith("data:"):
                    continue
                
                # Download image
                try:
                    img_data = self.session.get(src).content
                    img_name = os.path.basename(urlparse(src).path)
                    if not img_name: 
                        img_name = f"img_{len(downloaded_images)}.jpg"
                        
                    # Add to zip
                    zf.writestr(f"assets/{img_name}", img_data)
                    
                    # Update src in markdown to relative path
                    downloaded_images[src] = f"assets/{img_name}"
                    img['src'] = f"assets/{img_name}"
                except:
                    pass

            # 6. Decode Content (Text)
            raw_text = content_element.decode_contents()
            decoded_text = self.font_decoder.decode(raw_text)
            
            # Re-parse decoded text to soup to handle markdown conversion better?
            # Or just pass decoded text to markdownify if it accepts html string.
            # ddddocr operates on text, so we assume `decoded_text` is still HTML but with characters replaced.
            
            markdown_content = md(decoded_text)
            
            # Post-processing fixes (math, etc) can go here
            
            final_md = f"# {title}\n\nURL: {url}\n\n{markdown_content}"
            
            zf.writestr(f"{safe_title}.md", final_md)
            
        # Add timestamp to filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_filename = f"{safe_title}_{timestamp}.zip"
        
        mem_zip.seek(0)
        return (final_filename, mem_zip)

    def _extract_font_data(self, html):
        # Extract base64 fonts
        # Regex from original code: matches base64 font in @font-face
        matches = re.findall(r"@font-face\s*\{[^\}]*?src:\s*url\((?:data:font/(?:ttf|woff|woff2);charset=utf-8;base64,)?([A-Za-z0-9+/=]+)\)", html)
        
        # Convert base64 to bytes
        fonts = []
        for m in matches:
            try:
                fonts.append(base64.b64decode(m))
            except:
                pass
        
        # Original logic picked the 3rd one? We can try loading all, font_decoder handles it.
        # If multiple fonts map the same characters, last one wins.
        return fonts
