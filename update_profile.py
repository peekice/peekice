from datetime import datetime
from dotenv import load_dotenv, dotenv_values
import os
import base64
from requests import post, get
import json
import random
from bs4 import BeautifulSoup

load_dotenv()
env_path = ".env"
md_path = "README.md"
current_song_path = "current_song.txt"

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
playlist_id = os.getenv("PLAYLIST_ID")

strava_client_id = os.getenv("STRAVA_CLIENT_ID")
strava_client_secret = os.getenv("STRAVA_CLIENT_SECRET")
strava_refresh_token = os.getenv("STRAVA_REFRESH_TOKEN")

start_random_song = "<!-- Start random song -->"
end_random_song = "<!-- End random song -->"

start_last_activity = "<!-- Start last activity -->"
end_last_activity = "<!-- End last activity -->"


def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {"grant_type": "client_credentials"}

    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token


def get_auth_header(token):
    return {"Authorization": "Bearer " + token}


def add_song_to_readme(title, artist, img, link):

    with open(md_path, "r", encoding="utf-8") as file:
        content = file.readlines()

    start_line = (
        next((i for i, line in enumerate(content) if start_random_song in line), None)
        + 1
    )
    end_line = next(
        (i for i, line in enumerate(content) if end_random_song in line), None
    )

    replace_song = "".join(content[start_line:end_line])
    soup = BeautifulSoup(replace_song, "lxml")

    tag = {"title": title, "artist": artist, "image": img, "link": link}

    for t in tag:
        element = soup.find(id=t)
        if element:
            if element.name == "a":
                element["href"] = tag[t]
                img = element.find("img")
                img["src"] = tag["image"]
            else:
                element.string = tag[t]

    new_content = (
        "".join(content[:start_line])
        + str(soup.prettify()[15:-17])
        + "".join(content[end_line:])
    )

    with open(md_path, "w", encoding="utf-8") as file:
        file.write(new_content)


def get_current_song_id():
    with open(current_song_path, "r") as f:
        return f.read()


def add_current_song_id(song_id):
    with open(current_song_path, "w") as f:
        f.write(song_id)


def random_songs_from_playlist():
    token = get_token()
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = get_auth_header(token)

    result = get(url, headers=headers)
    tracks = result.json()["items"]

    current_song_id = get_current_song_id()
    available_tracks = [
        track for track in tracks if track["track"]["id"] != current_song_id
    ]

    new_song = random.choice(available_tracks)["track"]
    add_current_song_id(new_song["id"])

    title = new_song["name"]
    artist = new_song["artists"][0]["name"]
    img = new_song["album"]["images"][0]["url"]
    link = new_song["external_urls"]["spotify"]

    add_song_to_readme(title, artist, img, link)


def get_strava_access_token():

    response = post(
        url="https://www.strava.com/api/v3/oauth/token",
        data={
            "client_id": strava_client_id,
            "client_secret": strava_client_secret,
            "grant_type": "refresh_token",
            "refresh_token": strava_refresh_token,
        },
    )
    return response.json().get("access_token")


def add_activity_to_readme(
    activity_name, readable_date, activity_distance, activity_pace, activity_time_formatted
):
    with open(md_path, "r", encoding="utf-8") as file:
        content = file.readlines()

    start_line = (
        next((i for i, line in enumerate(content) if start_last_activity in line), None)
        + 1
    )
    end_line = next(
        (i for i, line in enumerate(content) if end_last_activity in line), None
    )

    html_pattern = f"""
<div align="center">
  <table border="0">
    <tr>
      <td align="center" colspan="3">
        <h2>🏃 My Latest Strava Activity</h2>
        <strong>{activity_name}</strong><br />
        <small>📅 {readable_date}</small>
      </td>
    </tr>
    <tr>
      <td width="150" align="center">
        <b>Distance</b><br />
        <img src="https://img.shields.io/badge/{activity_distance}-FC4C02?style=for-the-badge&logo=strava&logoColor=white" alt="Distance">
      </td>
      <td width="150" align="center">
        <b>Time</b><br />
        <img src="https://img.shields.io/badge/{activity_time_formatted}-03A9F4?logo=clockify&logoColor=fff&style=for-the-badge" alt="Pace">
      </td>
      <td width="150" align="center">
        <b>Pace</b><br />
        <img src="https://img.shields.io/badge/{activity_pace}_min/km-2D2D2D?style=for-the-badge&logo=speedtest&logoColor=white" alt="Pace">
      </td>
    </tr>
    <tr>
      <td align="center" colspan="3">
        <p>
          <a href="https://www.strava.com/athletes/153761910">
          <img src="https://img.shields.io/badge/Follow_on_Strava-FC4C02?style=flat-square&logo=strava&logoColor=white" alt="Follow on Strava">
          </a>
        </p>
      </td>
    </tr>
  </table>
</div>
"""

    new_content = (
        "".join(content[:start_line]) + html_pattern + "".join(content[end_line:])
    )

    with open(md_path, "w", encoding="utf-8") as file:
        file.write(new_content)


def get_activity_from_strava():
    access_token = get_strava_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    activity_url = "https://www.strava.com/api/v3/athlete/activities"
    response = get(activity_url, headers=headers)
    activities = response.json()

    recent_activity = activities[0]

    if recent_activity.get("type") == "Run":
        activity_name = recent_activity["name"]
        activity_date = recent_activity["start_date_local"]
        readable_date = datetime.strptime(activity_date, "%Y-%m-%dT%H:%M:%SZ")

        activity_distance = f'{recent_activity["distance"] / 1000:.2f} km'
        activity_avg_speed = recent_activity["average_speed"]
        pace_min_float = (1000 / activity_avg_speed) / 60
        pace_minutes = int(pace_min_float)
        pace_seconds = int((pace_min_float - pace_minutes) * 60)
        activity_pace = f'{pace_minutes}:{pace_seconds:02d}'

        activity_time = recent_activity["moving_time"]
        hours = activity_time // 3600
        minutes = (activity_time % 3600) // 60
        seconds = activity_time % 60
        if hours > 0:
            activity_time_formatted = f"{hours}h {minutes}m {seconds}s"
        else:
            activity_time_formatted = f"{minutes}m {seconds}s"

        add_activity_to_readme(
            activity_name, readable_date.strftime("%d %B, %Y"), activity_distance, activity_pace, activity_time_formatted
        )
    else:
        print("Last activity is not a run. No update made.")


if __name__ == "__main__":
    random_songs_from_playlist()
    get_activity_from_strava()
