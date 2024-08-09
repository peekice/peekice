from dotenv import load_dotenv, dotenv_values
import os
import base64
from requests import post,get
import json
import random
from bs4 import BeautifulSoup

load_dotenv()
env_path = '.env'
md_path = 'README.md'
current_song_path = 'current_song.txt'

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
playlist_id = os.getenv("PLAYLIST_ID")

start_comment = "<!-- Start random song -->"
end_comment = "<!-- End random song -->"

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {"grant_type": "client_credentials"} 

    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

def add_song_to_readme(title, artist, img, link):

    with open(md_path, 'r', encoding='utf-8') as file:
        content = file.readlines()

    start_line = next((i for i, line in enumerate(content) if start_comment in line), None) + 1
    end_line = next((i for i, line in enumerate(content) if end_comment in line), None)

    replace_song = ''.join(content[start_line:end_line])
    soup = BeautifulSoup(replace_song, 'lxml')

    tag = {"title": title, "artist": artist, "image": img, "link": link}

    for t in tag:
        element = soup.find(id=t)
        if element:
            if element.name == 'a':
                element['href'] = tag[t]
                img = element.find('img')
                img['src'] = tag['image']
            else:
                element.string = tag[t]

    new_content = ''.join(content[:start_line]) + str(soup.prettify()[15:-17]) + ''.join(content[end_line:])
    
    with open(md_path, 'w', encoding='utf-8') as file:
        file.write(new_content)

def get_current_song_id():
    with open(current_song_path, 'r') as f:
        return f.read()
    
def add_current_song_id(song_id):
    with open(current_song_path, 'w') as f:
        f.write(song_id)

def random_songs_from_playlist():
    token = get_token()
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = get_auth_header(token)

    result = get(url, headers=headers)
    tracks = result.json()['items']

    current_song_id = get_current_song_id()
    available_tracks = [track for track in tracks if track["track"]["id"] != current_song_id]
    
    new_song = random.choice(available_tracks)["track"]
    add_current_song_id(new_song["id"])

    title = new_song["name"]
    artist = new_song["artists"][0]["name"]
    img = new_song["album"]["images"][0]["url"]
    link =  new_song["external_urls"]["spotify"]

    add_song_to_readme(title, artist, img, link)

if __name__ == "__main__":
    random_songs_from_playlist()
