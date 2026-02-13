import os
from typing import Optional, Dict, Any

from yt_dlp import YoutubeDL


class YTV_Downloader:
    """YouTube Video下载器"""

    def __init__(self,
                 video_dir: str = "./video",
                 subtitle_dir: str = "./subtitle",
                 subtitle_lang: str = 'en'):
        """
        初始化YouTube下载客户端

        Args:
            video_dir: 视频保存目录，默认为"./video"
            subtitle_dir: 字幕保存目录，默认为"./subtitle"
            subtitle_lang: 字幕语言，默认为'en'
        """
        self.video_dir = video_dir
        self.subtitle_dir = subtitle_dir
        self.subtitle_lang = subtitle_lang

        # 确保目录存在
        os.makedirs(video_dir, exist_ok=True)
        os.makedirs(subtitle_dir, exist_ok=True)

    def download(self, url: str, **kwargs) -> Optional[str]:
        """
        下载视频和字幕

        Args:
            url: YouTube视频URL
            **kwargs: 额外的下载选项

        Returns:
            字幕文件路径（如果下载成功），否则返回None
        """
        # 合并默认选项和自定义选项
        ydl_opts = self._get_download_options(**kwargs)

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'video')

                # 生成字幕文件路径
                subtitle_path = os.path.join(self.subtitle_dir, f"{title}.{self.subtitle_lang}.srt")

                # 检查字幕文件是否存在
                if os.path.exists(subtitle_path):
                    print(f"下载完成: {title}")
                    print(f"\t视频保存到: {self.video_dir}/")
                    print(f"\t字幕保存到: {subtitle_path}")
                    return subtitle_path
                else:
                    print(f"字幕文件未生成: {subtitle_path}")
                    return None

        except Exception as e:
            print(f"下载失败: {e}")
            return None

    def _get_download_options(self, **kwargs) -> Dict[str, Any]:
        """获取下载配置选项"""
        # 基本配置
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'outtmpl': {
                'default': f'{self.video_dir}/%(title)s.%(ext)s',
                'subtitle': f'{self.subtitle_dir}/%(title)s.%(ext)s',
            },
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': [self.subtitle_lang],
            'subtitlesformat': 'srt',
            'ignoreerrors': True,
            'sleep_interval': 5,
            'max_sleep_interval': 10,
            'retries': 5,
            'quiet': False,
            'no_warnings': False,
        }

        # 合并自定义选项
        ydl_opts.update(kwargs)

        # Node.js配置（Windows环境）
        try:
            import platform
            if platform.system() == 'Windows':
                ydl_opts['js_runtimes'] = {
                    'node': {'path': r'D:\PF\nodejs\node.exe'}
                }
        except:
            pass

        return ydl_opts

    def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        获取视频信息（不下载）

        Args:
            url: YouTube视频URL

        Returns:
            视频信息字典
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'upload_date': info.get('upload_date', ''),
                    'thumbnail': info.get('thumbnail', ''),
                }
        except Exception as e:
            print(f"获取视频信息失败: {e}")
            return None

    def list_downloaded_videos(self) -> list:
        """列出已下载的视频文件"""
        videos = []
        for file in os.listdir(self.video_dir):
            if file.endswith('.mp4'):
                videos.append(os.path.join(self.video_dir, file))
        return videos

    def list_downloaded_subtitles(self) -> list:
        """列出已下载的字幕文件"""
        subtitles = []
        for file in os.listdir(self.subtitle_dir):
            if file.endswith('.srt'):
                subtitles.append(os.path.join(self.subtitle_dir, file))
        return subtitles



# =========================
# 使用示例
# =========================
if __name__ == '__main__':
    # 示例1：简单下载
    yt = YTV_Downloader()
    subtitle_path = yt.download("https://www.youtube.com/watch?v=example")