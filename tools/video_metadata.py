from typing import Optional, Dict, Any

from yt_dlp import YoutubeDL


class VideoMetadataTool:
    """
    YouTube视频信息获取工具
    """

    def __init__(self):

        self.ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True
        }

    def get_metadata(self, url: str) -> Optional[Dict[str, Any]]:
        """
        获取视频元数据（不下载视频）

        Returns:
            dict
        """

        try:

            with YoutubeDL(self.ydl_opts) as ydl:

                info = ydl.extract_info(url, download=False)

                if not info:
                    return None

                return {
                    "title": info.get("title"),
                    "uploader": info.get("uploader"),
                    "duration": info.get("duration"),
                    "view_count": info.get("view_count"),
                    "upload_date": info.get("upload_date"),
                    "description": info.get("description"),
                    "thumbnail": info.get("thumbnail"),
                    "webpage_url": info.get("webpage_url"),
                }

        except Exception as e:

            print("获取视频信息失败:", e)

            return None
