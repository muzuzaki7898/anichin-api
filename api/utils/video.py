import re
from .parsing import Parsing
from urllib.parse import urlparse, urlencode, parse_qsl
from dotenv import load_dotenv
import os
from base64 import b64decode
import logging
from typing import Dict, List, Optional, Any, Union
from bs4 import BeautifulSoup

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class Video(Parsing):
    def __init__(self, slug: str) -> None:
        super().__init__()
        self.slug: str = slug
        logger.info(f"Initialized Video scraper for slug: {slug}")

    def get_details(self) -> Union[Dict[str, Any], bool]:
        """Get video details for the specified slug."""
        try:
            logger.info(f"Starting to fetch video details for slug: {self.slug}")

            data = self.get_parsed_html(self.slug)
            if not data:
                logger.error("Failed to get video page data")
                return False

            video_data = self.__get_video(data)
            return video_data

        except Exception as e:
            logger.error(f"Error in get_details for slug {self.slug}: {e}")
            return False

   def __get_video(self, data: BeautifulSoup) -> Union[Dict[str, Any], bool]:
        """Extract video information from the page data."""
        try:
            # 1. JALUR BARU: Cari Iframe Dailymotion (Seperti temuanmu)
            iframe = data.find("iframe", src=re.compile(r"dailymotion\.com|geo\.dailymotion"))
            if iframe:
                logger.info("Found Dailymotion iframe!")
                return {"stream_url": iframe.get("src")}

            # 2. JALUR CADANGAN: Mirror Select (Kode originalmu)
            video_select = data.find("select", {"class": "mirror"})
            if video_select:
                options = video_select.find_all("option")
                if options:
                    # Cari OK.ru seperti di kode lamamu
                    okru_option = next((opt for opt in options if opt.text.strip() == "OK.ru"), None)
                    if okru_option and okru_option.get("value"):
                        # ... logika decoding base64 lamamu ...
                        video_value = okru_option["value"]
                        decoded_data = b64decode(video_value).decode("utf-8")
                        parsed_content = self.parsing(decoded_data)
                        iframe_ok = parsed_content.find("iframe")
                        if iframe_ok and iframe_ok.get("src"):
                            # Jalankan API fastsavenow kamu di sini
                            return self.__get_api_video(iframe_ok["src"].replace("videoembed", "video"))

            logger.warning("No video source found in any method")
            return False
        except Exception as e:
            logger.error(f"Error extracting video data: {e}")
            return False
        
    
    def __update_media_urls(
        self, results: Dict[str, Any], query_string: str
    ) -> Dict[str, Any]:
        """Update media URLs with additional query parameters."""
        try:
            if not isinstance(results, dict) or "medias" not in results:
                logger.warning("Invalid results format for media URL update")
                return results

            medias = results.get("medias", [])
            if not isinstance(medias, list):
                logger.warning("Medias is not a list")
                return results

            for media in medias:
                try:
                    if not isinstance(media, dict) or "url" not in media:
                        logger.warning("Invalid media format, skipping")
                        continue

                    url_parts = urlparse(media["url"])
                    query = dict(parse_qsl(url_parts.query))

                    # Parse and add new query parameters
                    new_params = dict(
                        param.split("=")
                        for param in query_string.split("&")
                        if "=" in param
                    )
                    query.update(new_params)

                    # Reconstruct URL
                    updated_url_parts = url_parts._replace(query=urlencode(query))
                    media["url"] = updated_url_parts.geturl()

                    logger.debug(f"Updated media URL: {media['url']}")

                except Exception as media_error:
                    logger.error(f"Error updating media URL: {media_error}")
                    continue

            logger.debug(f"Updated {len(medias)} media URLs")
            return results

        except Exception as e:
            logger.error(f"Error in __update_media_urls: {e}")
            return results


if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    video = Video("perfect-world-episode-03-subtitle-indonesia")
    print(video.get_details())
