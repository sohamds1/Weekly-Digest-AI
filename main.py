import os
import datetime
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import google.generativeai as genai
from github import Github

# --- CONFIGURATION ---
# These values are pulled from the GitHub Secrets/Environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PLAYLIST_ID = os.environ.get("PLAYLIST_ID")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") # Automatically provided by GitHub Actions
REPO_NAME = os.environ.get("GITHUB_REPOSITORY") # Automatically provided (e.g., "yourname/project")

def get_video_ids_from_playlist(playlist_id):
    # Note: To keep this strictly "no-code/lazy" and avoid needing a YouTube API Key,
    # we are using a trick. Ideally, you use YouTube Data API, but that requires more setup.
    # For a lazy hobby project, we will use `youtube_transcript_api` to try and fetch.
    # HOWEVER, without the YouTube Data API, getting a list of *new* videos is hard.
    #
    # COMPROMISE: For the absolute simplest path, we will use a public library
    # 'scrapetube' (add to requirements) or just assume you want the latest videos.
    # Let's use a robust scraping method for the playlist to avoid API limits.
    
    # Actually, to keep it 100% free and simple, we will stick to the 'youtube-transcript-api' 
    # but we need a way to get video IDs.
    # Let's add 'scrapetube' to requirements for easy playlist fetching without an API key.
    import scrapetube
    videos = scrapetube.get_playlist(playlist_id)
    
    # Get videos from the last 7 days? 
    # Scrapetube doesn't give exact dates easily, so we'll grab the last 5 videos 
    # and let the LLM decide if they are relevant or you can just read the latest 5.
    return [video['videoId'] for video in list(videos)[:5]] 

def get_transcripts(video_ids):
    transcript_text = ""
    formatter = TextFormatter()
    
    for video_id in video_ids:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            formatted = formatter.format_transcript(transcript)
            transcript_text += f"\n\n--- VIDEO ID: {video_id} ---\n{formatted}"
        except Exception as e:
            print(f"Could not fetch transcript for {video_id}: {e}")
            
    return transcript_text

def summarize_with_gemini(text):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash') # Flash is faster/cheaper/good enough
    
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
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    repo.create_issue(title=f"Weekly Digest: {date_str}", body=content)

if __name__ == "__main__":
    # 1. Get Video IDs
    print("Fetching videos...")
    import scrapetube # Import here to ensure it's installed
    video_ids = get_video_ids_from_playlist(PLAYLIST_ID)
    
    if not video_ids:
        print("No videos found.")
        exit()

    # 2. Get Transcripts
    print("Fetching transcripts...")
    full_text = get_transcripts(video_ids)
    
    if len(full_text) < 50:
        print("Not enough transcript data found.")
        exit()

    # 3. Summarize
    print("Summarizing...")
    summary = summarize_with_gemini(full_text)
    
    # 4. Post Issue
    print("Posting to GitHub...")
    create_github_issue(summary)
    print("Done!")
