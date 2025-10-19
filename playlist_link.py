import yt_dlp

def get_video_links_from_playlist(playlist_url):
    # Create a YT-DLP object
    ydl_opts = {
        'quiet': True,  # Suppress unnecessary output
        'extract_flat': True,  # Don't download the videos, just get their info
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Extract playlist info
        result = ydl.extract_info(playlist_url, download=False)

        # Check if it's a playlist
        if 'entries' in result:
            video_urls = [entry['url'] for entry in result['entries']]
            return video_urls
        else:
            return None

playlist_url = 'https://www.youtube.com/playlist?list=PLu0QvMsJToc122Tf51KEvtpborrlhvMIu'
video_links = get_video_links_from_playlist(playlist_url)

print(video_links)
