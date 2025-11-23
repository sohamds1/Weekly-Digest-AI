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
    # Use RSS feed to get video IDs (Works for Unlisted/Public)
    rss_url = f"https://www.youtube.com/feeds/videos.xml?playlist_id={playlist_id}"
    try:
        response = requests.get(rss_url)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        ns = {'yt': 'http://www.youtube.com/xml/schemas/2015', 'atom': 'http://www.w3.org/2005/Atom'}
        video_ids = []
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
            # THE FIX: Use list_transcripts to find ANY English version (Auto or Manual)
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # This logic says: "Find English. If manual doesn't exist, give me the Auto-generated one."
            # It looks for 'en' (Standard English), 'en-US', or 'en-GB'
            transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
            
            # Fetch the actual text
            final_data = transcript.fetch()
            formatted = formatter.format_transcript(final_data)
            
            transcript_text += f"\n\n--- VIDEO ID: {video_id} ---\n{formatted}"
            print(f"✅ Success: {video_id} (Type: {'Manual' if not transcript.is_generated else 'Auto-Generated'})")
            
        except Exception as e:
            # If English fails, we try one last desperation move: The default translation
            print(f"⚠️ Primary English failed for {video_id}, trying generic auto-caption...")
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                # Just get the first available one (even if it's auto-generated English)
                transcript = next(iter(transcript_list))
                final_data = transcript.fetch()
                formatted = formatter.format_transcript(final_data)
                transcript_text += f"\n\n--- VIDEO ID: {video_id} ---\n{formatted}"
                print(f"✅ Success (Fallback): {video_id}")
            except:
                print(f"❌ Totally Failed {video_id}: {e}")
            
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
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "Error generating summary."

def create_github_issue(content):
    if not content or content == "Error generating summary.":
        print("No valid content to publish.")
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
        exit()

    # 2. Get Transcripts
    full_text = get_transcripts(video_ids)
    
    if len(full_text) < 50:
        print("Not enough transcript data found. (Maybe videos have no captions?)")
        exit()

    # 3. Summarize
    print("Summarizing...")
    summary = summarize_with_gemini(full_text)
    
    # 4. Post Issue
    print("Posting to GitHub...")
    create_github_issue(summary)
    print("Done!")