import os
from typing import Optional, Dict, Any

from yt_dlp import YoutubeDL

from config.settings import VIDEO_DIR, SUBTITLE_DIR


class YouTubeDownloader:
    """
    YouTube 视频与字幕下载工具
    """

    def __init__(self, subtitle_lang: str = "en"):

        self.video_dir = VIDEO_DIR
        self.subtitle_dir = SUBTITLE_DIR
        self.subtitle_lang = subtitle_lang

        os.makedirs(self.video_dir, exist_ok=True)
        os.makedirs(self.subtitle_dir, exist_ok=True)

    def download(self, url: str) -> Optional[str]:
        """
        下载视频和字幕

        Returns
        -------
        str | None
            返回字幕文件路径
        """

        ydl_opts = self._get_options()

        try:
            with YoutubeDL(ydl_opts) as ydl:

                info = ydl.extract_info(url, download=True)

                title = info.get("title", "video")

                subtitle_path = os.path.join(
                    self.subtitle_dir,
                    f"{title}.{self.subtitle_lang}.srt"
                )

                if os.path.exists(subtitle_path):

                    print(f"下载完成: {title}")
                    print(f"视频目录: {self.video_dir}")
                    print(f"字幕文件: {subtitle_path}")

                    return subtitle_path

                print("字幕未生成")

                return None

        except Exception as e:

            print(f"下载失败: {e}")

            return None

    def _get_options(self) -> Dict[str, Any]:

        ydl_opts = {

            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",

            "outtmpl": {
                "default": f"{self.video_dir}/%(title)s.%(ext)s",
                "subtitle": f"{self.subtitle_dir}/%(title)s.%(ext)s",
            },

            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": [self.subtitle_lang],
            "subtitlesformat": "srt",

            "ignoreerrors": True,
            "retries": 5,

            "quiet": False,
        }

        return ydl_opts

    def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        获取视频信息（不下载）
        """

        opts = {
            "quiet": True,
            "no_warnings": True,
        }

        try:

            with YoutubeDL(opts) as ydl:

                info = ydl.extract_info(url, download=False)

                return {
                    "title": info.get("title"),
                    "duration": info.get("duration"),
                    "views": info.get("view_count"),
                    "uploader": info.get("uploader"),
                    "thumbnail": info.get("thumbnail"),
                }

        except Exception as e:

            print(f"获取视频信息失败: {e}")

            return None