import os
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
from dotenv import load_dotenv
import re
from typing import List, Optional
from datetime import datetime

# Load environment variables
load_dotenv()

def get_youtube_client():
    """Create and return a YouTube API client"""
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        raise ValueError("YouTube API key not found. Please set YOUTUBE_API_KEY in your .env file")
    return build('youtube', 'v3', developerKey=api_key)

def extract_playlist_videos(playlist_url: str, exclude_pattern: str = "Naruhodo Entrevista") -> List[str]:
    """
    Extract all video URLs from a YouTube playlist,
    excluding videos with titles matching the exclude pattern.
    """
    try:
        # Extract playlist ID from URL
        playlist_id = re.search(r'list=([^&]+)', playlist_url)
        if not playlist_id:
            raise ValueError("Invalid playlist URL. Must contain 'list=' parameter")
        playlist_id = playlist_id.group(1)
        
        youtube = get_youtube_client()
        filtered_urls = []
        excluded_count = 0
        included_count = 0
        next_page_token = None
        
        print("Processing playlist...")
        
        while True:
            request = youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            
            for item in response['items']:
                try:
                    video_id = item['snippet']['resourceId']['videoId']
                    title = item['snippet']['title']
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    if exclude_pattern and exclude_pattern in title:
                        excluded_count += 1
                        print(f"Excluding: {title}")
                    else:
                        filtered_urls.append(url)
                        included_count += 1
                        print(f"Including: {title}")
                        
                except Exception as e:
                    print(f"Error processing video: {str(e)}")
                    continue
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        
        print(f"\nTotal videos to process: {included_count}")
        print(f"Total videos excluded: {excluded_count}")
        
        return filtered_urls
    
    except Exception as e:
        print(f"Error extracting playlist: {str(e)}")
        return []

def extract_youtube_transcript(video_url: str, output_dir: str = "transcripts") -> Optional[str]:
    """Extract transcript from a YouTube video"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        # Extract video ID
        if "youtube.com" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        elif "youtu.be" in video_url:
            video_id = video_url.split("/")[-1].split("?")[0]
        else:
            print(f"Invalid YouTube URL: {video_url}")
            return None
        
        # Get video details
        youtube = get_youtube_client()
        video_response = youtube.videos().list(
            part="snippet",
            id=video_id
        ).execute()
        
        if not video_response['items']:
            print(f"Video not found: {video_id}")
            return None
            
        video_title = video_response['items'][0]['snippet']['title']
        
        # Get transcript
        transcript_list = None
        language_code = None
        
        # Try to get Portuguese transcript (including auto-generated)
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt'])
            language_code = 'pt'
            print("Using Portuguese transcript")
        except:
            try:
                # Try auto-generated Portuguese
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt-PT', 'pt-BR'])
                language_code = 'pt-auto'
                print("Using auto-generated Portuguese transcript")
            except Exception as e:
                print(f"Could not get Portuguese transcript: {str(e)}")
                return None
        
        if not transcript_list:
            print(f"No transcript available for: {video_title}")
            return None
        
        # Format transcript
        formatted_transcript = []
        formatted_transcript.append(f"Title: {video_title}")
        formatted_transcript.append(f"URL: {video_url}")
        formatted_transcript.append(f"Language: {language_code}")
        formatted_transcript.append(f"Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        formatted_transcript.append("=" * 80)
        formatted_transcript.append("")  # Empty line
        
        # Process transcript entries
        for entry in transcript_list:
            start = float(entry['start'])
            minutes = int(start // 60)
            seconds = int(start % 60)
            timestamp = f"[{minutes:02d}:{seconds:02d}]"
            text = str(entry['text']).strip()
            formatted_transcript.append(f"{timestamp} {text}\n")
        
        # Save to file
        safe_title = "".join([c if c.isalnum() or c in ' -_' else '_' for c in video_title])
        safe_title = safe_title[:50]  # Limit filename length
        output_file = os.path.join(output_dir, f"{safe_title}_{video_id}_{language_code}.txt")
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(formatted_transcript))
        
        print(f"✓ Transcript saved: {os.path.basename(output_file)}")
        return output_file
        
    except Exception as e:
        print(f"✗ Error extracting transcript for {video_id}: {str(e)}")
        return None

def process_playlist_transcripts(playlist_url: str, exclude_pattern: str = "Naruhodo Entrevista", output_dir: str = "transcripts") -> None:
    """Process all videos in a playlist and download their transcripts"""
    video_urls = extract_playlist_videos(playlist_url, exclude_pattern)
    
    if not video_urls:
        print("No videos to process.")
        return
    
    successful = 0
    failed = 0
    
    print(f"\nDownloading transcripts to '{output_dir}' folder...")
    
    for i, url in enumerate(video_urls):
        print(f"\nProcessing video {i+1}/{len(video_urls)}: {url}")
        transcript_file = extract_youtube_transcript(url, output_dir)
        
        if transcript_file:
            successful += 1
        else:
            failed += 1
    
    print(f"\nProcessing complete!")
    print(f"Successfully downloaded: {successful} transcripts")
    print(f"Failed to download: {failed} transcripts")
    print(f"Transcripts saved to: {os.path.abspath(output_dir)}")

# Example usage
if __name__ == "__main__":
    # Replace with your playlist URL
    playlist_url = "https://www.youtube.com/watch?v=wIPj3OjsFEI&list=PLZjaOxYREinv5RgR-T1ObnljITmsPIZWa"
    process_playlist_transcripts(playlist_url)

# Optional: Test function for single video
def test_transcript_extraction(video_url: str):
    """Test transcript extraction for a single video"""
    try:
        # Extract video ID
        if "youtube.com" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        elif "youtu.be" in video_url:
            video_id = video_url.split("/")[-1].split("?")[0]
        else:
            print(f"Invalid URL: {video_url}")
            return
        
        print(f"Getting transcript for video ID: {video_id}")
            
        # Get list of available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        print("\nAvailable transcripts:")
        for transcript in transcript_list:
            print(f"- {transcript.language_code} ({transcript.language})")
        
        # Try to get Portuguese transcript (including auto-generated)
        transcript = None
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt'])
            print("\nUsing Portuguese transcript")
        except:
            try:
                # Try auto-generated Portuguese
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt-PT', 'pt-BR'])
                print("\nUsing auto-generated Portuguese transcript")
            except Exception as e:
                print(f"\nCould not get Portuguese transcript: {str(e)}")
                return
        
        if transcript:
            # Print first few entries
            print("\nFirst 3 entries of transcript:")
            for entry in transcript[:3]:
                minutes = int(float(entry['start']) // 60)
                seconds = int(float(entry['start']) % 60)
                print(f"[{minutes:02d}:{seconds:02d}] {entry['text']}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

# Test with a single video (optional)
# test_url = "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
# test_transcript_extraction(test_url)