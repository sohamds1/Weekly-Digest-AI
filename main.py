import os
import datetime
import requests
import xml.etree.ElementTree as ET
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import google.generativeai as genai
from github import Github

# --- CONFIGURATION ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PLAYLIST_ID = os.environ.get("PLAYLIST_ID")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")

def get_video_ids_from_playlist(playlist_id):
    # THE FIX: Use YouTube's hidden RSS feed instead of scraping.
    # This works for Public and Unlisted playlists and is much more stable.
    rss_url = f"https://www.youtube.com/feeds/videos.xml?playlist_id={playlist_id}"
    
    try:
        response = requests.get(rss_url)
        response.raise_for_status() # Check for errors (like 404/Private)
        
        # Parse the XML
        root = ET.fromstring(response.content)
        ns = {'yt': 'http://www.youtube.com/xml/schemas/2015', 'media': 'http://search.yahoo.com/mrss/', 'atom': 'http://www.w3.org/2005/Atom'}
        
        video_ids = []
        # The RSS feed returns the last 15 videos. Perfect for a weekly digest.
        for entry in root.findall('atom:entry', ns):
            video_id = entry.find('yt:videoId', ns).text
            video_ids.append(video_id)
            
        return video_ids

    except Exception as e:
        print(f"Error fetching playlist: {e}")
        return []

def get_transcripts(video_ids):
    transcript_text = ""
    formatter = TextFormatter()
    
    print(f"Attempting to fetch transcripts for {len(video_ids)} videos...")
    
    for video_id in video_ids:
        try:
            # We fetch the transcript
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            formatted = formatter.format_transcript(transcript)
            transcript_text += f"\n\n--- VIDEO ID: {video_id} ---\n{formatted}"
            print(f"✅ Success: {video_id}")
        except Exception as e:
            # Often videos don't have captions. We skip them without crashing.
            print(f"⚠️ Skipped {video_id} (No captions or error): {e}")
            
    return transcript_text

def summarize_with_gemini(text):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash') 
    
    prompt = f"""
    You are a newsletter editor. Below are transcripts from the latest videos in my curated playlist.
    
    Task: Create a weekly digest.
    1. Title: Catchy title for this week.
    2. Intro: 1 sentence on the common theme.
    3. For each distinct video topic found:
       - **Headline** (Video Title/Topic)
       - **TL;DR:** 2 sentences summary.
       - **Key Insight:** The most valuable point.
    4. Tone: Casual, poignant, easy to absorb.
    5. Format: Markdown.
    
    Transcripts:
    {text}
    """
    
    response = model.generate_content(prompt)
    return response.text

def create_github_issue(content):
    if not content:
        print("No content to publish.")
        return

    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    repo.create_issue(title=f"Weekly Digest: {date_str}", body=content)

if __name__ == "__main__":
    # 1. Get Video IDs
    print(f"Fetching videos from Playlist: {PLAYLIST_ID}")
    video_ids = get_video_ids_from_playlist(PLAYLIST_ID)
    
    if not video_ids:
        print("No videos found. Check if Playlist is Private or Empty.")
        exit() # Exit cleanly

    # 2. Get Transcripts
    full_text = get_transcripts(video_ids)
    
    if len(full_text) < 50:
        print("Not enough transcript data found. (Maybe videos have no captions?)")
        exit()

    # 3. Summarize
    print("Summarizing...")
    try:
        summary = summarize_with_gemini(full_text)
        
        # 4. Post Issue
        print("Posting to GitHub...")
        create_github_issue(summary)
        print("Done!")
    except Exception as e:
        print(f"Error during summarization: {e}")
