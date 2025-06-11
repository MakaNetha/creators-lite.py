import streamlit as st
import pandas as pd
import requests
import json
from io import StringIO
import openai

# === CONFIGURATION ===
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

openai.api_key = OPENAI_API_KEY

# CPM data example
CPM_DATA = {
    "US": {"Beauty": 18.5, "Fitness": 15.0, "Finance": 25.3, "Tech": 20.1},
    "ZA": {"Beauty": 6.3, "Fitness": 5.5, "Finance": 8.2, "Tech": 7.5},
    "IN": {"Beauty": 5.2, "Fitness": 4.8, "Finance": 6.1, "Tech": 6.5},
}

def calculate_rpm(country, niche):
    base_cpm = CPM_DATA.get(country, {}).get(niche, 0)
    rpm = round(base_cpm * 0.55, 2)  # Simplified estimate
    return rpm, base_cpm

def fetch_youtube_trending_videos(niche, max_results=5):
    # Search for videos matching niche keyword, ordered by view count (proxy for trending)
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": YOUTUBE_API_KEY,
        "q": niche,
        "part": "snippet",
        "type": "video",
        "maxResults": max_results,
        "order": "viewCount",
        "regionCode": "US",  # Adjust region if needed
    }
    response = requests.get(search_url, params=params)
    if response.status_code != 200:
        return []
    data = response.json()
    videos = []
    for item in data.get("items", []):
        video = {
            "title": item["snippet"]["title"],
            "channel": item["snippet"]["channelTitle"],
            "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
            "videoId": item["id"]["videoId"],
        }
        videos.append(video)
    return videos

def openai_completion(prompt, max_tokens=100):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"OpenAI API error: {e}"

def generate_retention_strategy(niche):
    prompt = f"Suggest 3 effective YouTube video retention strategies for the niche '{niche}'."
    return openai_completion(prompt)

def generate_thumbnail_concept(niche):
    prompt = f"Generate a catchy and effective YouTube thumbnail concept idea for videos about '{niche}'."
    return openai_completion(prompt)

def to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

def main():
    st.set_page_config(page_title="Creator Lite - YouTube Niche Analyzer", layout="wide")
    st.title("📊 Creator Lite - YouTube Niche Analyzer & RPM Estimator")

    # Sidebar inputs
    st.sidebar.header("Settings")
    country = st.sidebar.selectbox("Select Country", list(CPM_DATA.keys()))
    niche = st.sidebar.selectbox("Select Niche", list(CPM_DATA[country].keys()))

    st.sidebar.markdown("---")
    max_results = st.sidebar.slider("Number of trending videos to fetch", min_value=3, max_value=10, value=5)

    # Calculate RPM
    rpm, cpm = calculate_rpm(country, niche)

    # Show CPM/RPM
    st.markdown(f"### Estimated CPM and RPM for **{niche}** in **{country}**")
    col1, col2 = st.columns(2)
    col1.metric("CPM ($)", f"{cpm}")
    col2.metric("RPM ($)", f"{rpm}")

    # Fetch trending videos for niche
    st.markdown(f"### 🔥 Top {max_results} Trending YouTube Videos in '{niche}'")
    videos = fetch_youtube_trending_videos(niche, max_results=max_results)

    if not videos:
        st.warning("Could not fetch YouTube data. Check API key or quota.")
    else:
        for v in videos:
            with st.container():
                st.markdown(f"**[{v['title']}](https://www.youtube.com/watch?v={v['videoId']})** by *{v['channel']}*")
                st.image(v['thumbnail'], width=320)
                st.markdown("---")

    # Retention strategy suggestion
    if st.button("Generate Retention Strategy Suggestions"):
        with st.spinner("Contacting OpenAI for retention strategies..."):
            strategy = generate_retention_strategy(niche)
            st.markdown("### Retention Strategy Suggestions:")
            st.write(strategy)

    # Thumbnail concept generator
    if st.button("Generate Thumbnail Concept Idea"):
        with st.spinner("Contacting OpenAI for thumbnail concept..."):
            thumbnail_concept = generate_thumbnail_concept(niche)
            st.markdown("### Thumbnail Concept Idea:")
            st.write(thumbnail_concept)

    # Prepare CSV report data
    report_data = []
    for v in videos:
        report_data.append({
            "Title": v['title'],
            "Channel": v['channel'],
            "Video URL": f"https://www.youtube.com/watch?v={v['videoId']}",
            "Thumbnail URL": v['thumbnail'],
            "Country": country,
            "Niche": niche,
            "CPM": cpm,
            "RPM": rpm,
        })
    df_report = pd.DataFrame(report_data)

    csv_data = to_csv(df_report)
    st.download_button(
        label="Download Niche Report CSV",
        data=csv_data,
        file_name=f"niche_report_{country}_{niche}.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()
