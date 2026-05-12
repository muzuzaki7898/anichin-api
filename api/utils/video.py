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
        """Extract video information with Dailymotion and Legacy Support."""
        try:
            # 1. CEK DAILYMOTION (Jalur Utama Baru)
            # Mencari iframe yang mengandung kata dailymotion
            iframe_dm = data.find("iframe", src=re.compile(r"dailymotion\.com|geo\.dailymotion"))
            if iframe_dm and iframe_dm.get("src"):
                logger.info("Dailymotion source detected")
                return {"stream_url": iframe_dm.get("src")}

            # 2. CEK MIRROR SELECT (Jalur Lama / Original)
            video_select = data.find("select", {"class": "mirror"})
            if video_select:
                options = video_select.find_all("option")
                # Cari opsi OK.ru
                okru_option = next((opt for opt in options if "OK.ru" in opt.text), None)
                
                if okru_option and okru_option.get("value"):
                    try:
                        video_value = okru_option["value"]
                        # Decode Base64
                        decoded_url = b64decode(video_value).decode("utf-8")
                        
                        # Parsing HTML hasil decode untuk ambil iframe src
                        soup_inner = BeautifulSoup(decoded_url, 'html.parser')
                        iframe_inner = soup_inner.find("iframe")
                        
                        if iframe_inner and iframe_inner.get("src"):
                            target_url = iframe_inner["src"].replace("videoembed", "video")
                            # Panggil fungsi API original kamu
                            return self.__get_api_video(target_url)
                    except Exception as b64_err:
                        logger.error(f"Error decoding legacy mirror: {b64_err}")

            # 3. JIKA SEMUA GAGAL, CARI IFRAME APAPUN (Last Resort)
            any_iframe = data.find("iframe")
            if any_iframe and any_iframe.get("src"):
                return {"stream_url": any_iframe.get("src")}

            return False

        except Exception as e:
            logger.error(f"Critical error in __get_video: {e}")
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
                
