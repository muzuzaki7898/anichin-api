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
        """Extract video information including Dailymotion support."""
        try:
            # 1. Cek apakah ada Iframe Dailymotion (Seperti yang kamu temukan)
            iframe = data.find("iframe", src=re.compile(r"dailymotion\.com|geo\.dailymotion"))
            if iframe:
                logger.info("Dailymotion iframe found!")
                return {"stream_url": iframe.get("src")}

            # 2. Jika tidak ada, coba cari iframe umum lainnya
            all_iframes = data.find_all("iframe")
            for f in all_iframes:
                src = f.get("src")
                if src and "http" in src:
                    return {"stream_url": src}

            # 3. Jalur lama (Mirror Select) tetap dipertahankan sebagai cadangan
            video_select = data.find("select", {"class": "mirror"})
            if video_select:
                # ... masukkan kode originalmu yang pakai FastSaveNow di sini ...
                pass

            return False
        except Exception as e:
            logger.error(f"Error extracting video: {e}")
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
