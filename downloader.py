import os
import yt_dlp
import requests
from urllib.parse import urlparse
import subprocess
import tempfile

class VideoDownloader:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
    
    def get_video_info(self, url, platform):
        """الحصول على معلومات الفيديو"""
        try:
            if platform == 'youtube':
                return self._get_youtube_info(url)
            elif platform == 'instagram':
                return self._get_instagram_info(url)
            elif platform == 'tiktok':
                return self._get_tiktok_info(url)
            elif platform in ['facebook', 'twitter']:
                return self._get_generic_info(url)
            else:
                return self._get_generic_info(url)
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def _get_youtube_info(self, url):
        """معلومات فيديو YouTube"""
        ydl_opts = {
            **self.ydl_opts,
            'format': 'best',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = info.get('formats', [])
            qualities = []
            for fmt in formats:
                if fmt.get('vcodec') != 'none' and fmt.get('ext') == 'mp4':
                    quality = fmt.get('format_note', fmt.get('height', 'unknown'))
                    if quality and quality not in qualities:
                        qualities.append(str(quality))
            
            return {
                'title': info.get('title', 'غير معروف'),
                'duration': self._format_duration(info.get('duration', 0)),
                'views': info.get('view_count', 0),
                'likes': info.get('like_count', 0),
                'thumbnail': info.get('thumbnail', ''),
                'qualities': sorted(set(qualities), reverse=True)[:10],
                'url': url
            }
    
    def _get_instagram_info(self, url):
        """معلومات فيديو Instagram"""
        try:
            # استخدام yt-dlp لإنستجرام
            ydl_opts = {
                **self.ydl_opts,
                'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'title': info.get('title', 'Instagram Video'),
                    'duration': self._format_duration(info.get('duration', 0)),
                    'views': info.get('view_count', 0),
                    'likes': info.get('like_count', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'qualities': ['default'],
                    'url': url
                }
        except:
            # استخدام طريقة بديلة
            return {
                'title': 'Instagram Video',
                'duration': 'غير معروف',
                'views': 'غير معروف',
                'likes': 'غير معروف',
                'qualities': ['default'],
                'url': url
            }
    
    def _get_tiktok_info(self, url):
        """معلومات فيديو TikTok"""
        try:
            ydl_opts = {
                **self.ydl_opts,
                'extract_flat': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'title': info.get('title', 'TikTok Video'),
                    'duration': self._format_duration(info.get('duration', 0)),
                    'views': info.get('view_count', 0),
                    'likes': info.get('like_count', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'qualities': ['default'],
                    'url': url
                }
        except:
            return {
                'title': 'TikTok Video',
                'duration': 'غير معروف',
                'views': 'غير معروف',
                'likes': 'غير معروف',
                'qualities': ['default'],
                'url': url
            }
    
    def _get_generic_info(self, url):
        """معلومات عامة للفيديو"""
        return {
            'title': 'Video Download',
            'duration': 'غير معروف',
            'views': 'غير معروف',
            'likes': 'غير معروف',
            'qualities': ['default'],
            'url': url
        }
    
    def download_video(self, url, platform, quality='default'):
        """تحميل الفيديو"""
        try:
            # إعداد خيارات yt-dlp حسب المنصة
            ydl_opts = {
                'outtmpl': os.path.join(self.temp_dir, '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'merge_output_format': 'mp4',
            }
            
            # إعدادات خاصة بكل منصة
            if platform == 'youtube':
                if quality != 'default':
                    ydl_opts['format'] = f'best[height<={quality}]'
                else:
                    ydl_opts['format'] = 'best[ext=mp4]'
            
            elif platform == 'instagram':
                ydl_opts['format'] = 'best'
            
            elif platform == 'tiktok':
                ydl_opts['format'] = 'best'
            
            # تحميل الفيديو
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # التأكد من امتداد mp4
                if not filename.endswith('.mp4'):
                    mp4_filename = filename.rsplit('.', 1)[0] + '.mp4'
                    if os.path.exists(filename):
                        os.rename(filename, mp4_filename)
                        filename = mp4_filename
                
                return filename
                
        except Exception as e:
            print(f"Download error: {e}")
            return None
    
    def _format_duration(self, seconds):
        """تنسيق المدة"""
        if not seconds:
            return "غير معروف"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
