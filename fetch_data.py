import pybaseball
import pandas as pd
import requests
from PIL import Image, ImageFile
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed

pybaseball.cache.enable()


MLB_TEAMS = [
    {"team": "AZ", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/ari.png&h=500&w=500"},
    {"team": "ATL", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/atl.png&h=500&w=500"},
    {"team": "BAL", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/bal.png&h=500&w=500"},
    {"team": "BOS", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/bos.png&h=500&w=500"},
    {"team": "CHC", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/chc.png&h=500&w=500"},
    {"team": "CWS", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/chw.png&h=500&w=500"},
    {"team": "CIN", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/cin.png&h=500&w=500"},
    {"team": "CLE", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/cle.png&h=500&w=500"},
    {"team": "COL", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/col.png&h=500&w=500"},
    {"team": "DET", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/det.png&h=500&w=500"},
    {"team": "HOU", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/hou.png&h=500&w=500"},
    {"team": "KC", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/kc.png&h=500&w=500"},
    {"team": "LAA", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/laa.png&h=500&w=500"},
    {"team": "LAD", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/lad.png&h=500&w=500"},
    {"team": "MIA", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/mia.png&h=500&w=500"},
    {"team": "MIL", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/mil.png&h=500&w=500"},
    {"team": "MIN", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/min.png&h=500&w=500"},
    {"team": "NYM", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/nym.png&h=500&w=500"},
    {"team": "NYY", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/nyy.png&h=500&w=500"},
    {"team": "OAK", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/oak.png&h=500&w=500"},
    {"team": "PHI", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/phi.png&h=500&w=500"},
    {"team": "PIT", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/pit.png&h=500&w=500"},
    {"team": "SD", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/sd.png&h=500&w=500"},
    {"team": "SF", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/sf.png&h=500&w=500"},
    {"team": "SEA", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/sea.png&h=500&w=500"},
    {"team": "STL", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/stl.png&h=500&w=500"},
    {"team": "TB", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/tb.png&h=500&w=500"},
    {"team": "TEX", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/tex.png&h=500&w=500"},
    {"team": "TOR", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/tor.png&h=500&w=500"},
    {"team": "WSH", "logo_url": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/scoreboard/wsh.png&h=500&w=500"}
]

df_image = pd.DataFrame(MLB_TEAMS)
IMAGE_DICT = df_image.set_index('team')['logo_url'].to_dict()

'''
start_dt, end_dt -> Date given by YYYY-MM-DD
pitcher -> First, last of pitcher (eg. Paul Skenes, Tarik Skubal, Huascar Brazoban) really tried to sneak in skubal there
'''
def pitch_data(start_dt: str, pitcher: str, end_dt: str | None = None) -> pd.DataFrame:
    
    try:
        first, last = pitcher.split(" ")

        # Fuzzy search so special chars in names dont give us a hard time
        player_id = pybaseball.playerid_lookup(last, first, fuzzy=True)['key_mlbam'].head(1).item() 
        
        if not end_dt:
            end_dt = start_dt

        daily_stats = pybaseball.statcast_pitcher(start_dt=start_dt, end_dt=end_dt, player_id=player_id)

        return daily_stats
    except:
        raise RuntimeError("Failed to retrieve pitch data")
    
def get_game_ids(date: str) -> list[int]:
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}"
    response = requests.get(url).json()
    
    return [
        game["gamePk"]
        for date_entry in response.get("dates", [])
        for game in date_entry.get("games", [])
    ]

def daily_pitches(date: str) -> pd.DataFrame:
    game_ids = get_game_ids(date)

    with ThreadPoolExecutor(max_workers=len(game_ids)) as executor:
        futures = {executor.submit(pybaseball.statcast_single_game, gid): gid for gid in game_ids}
        results = []
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                print(f"Failed for game {futures[future]}: {e}")

    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()
    
def player_headshot(player_id: str) -> ImageFile:
    url = f'https://img.mlbstatic.com/mlb-photos/image/'\
          f'upload/d_people:generic:headshot:67:current.png'\
          f'/w_640,q_auto:best/v1/people/{player_id}/headshot/silo/current.png'

    
    response = requests.get(url)

    if response.status_code != 200:
        raise RuntimeError("Failed to fetch player headshot from API")

    # Open the image from the response content
    return Image.open(BytesIO(response.content))

def player_bio(player_id: str) -> tuple:

    url = f"https://statsapi.mlb.com/api/v1/people?personIds={player_id}&hydrate=currentTeam"

    # GET request
    data = requests.get(url).json()

    # Extract player information from the JSON data
    player_name = data['people'][0]['fullName']
    throwing_hand = data['people'][0]['pitchHand']['code']
    age = data['people'][0]['currentAge']
    height = data['people'][0]['height']
    weight = data['people'][0]['weight']

    return (player_name, throwing_hand, age, height, weight)

def team_logo(pitcher_id: str) -> ImageFile:

    url = f"https://statsapi.mlb.com/api/v1/people?personIds={pitcher_id}&hydrate=currentTeam"

    # GET request
    data = requests.get(url).json()

    # Construct the URL to fetch team data
    url_team = 'https://statsapi.mlb.com/' + data['people'][0]['currentTeam']['link']

    # Send a GET request to the team URL and parse the JSON response
    data_team = requests.get(url_team).json()

    # Extract the team abbreviation
    team_abb = data_team['teams'][0]['abbreviation']

    # Get the logo URL from the image dictionary using the team abbreviation
    logo_url = IMAGE_DICT[team_abb]

    # Send a GET request to the logo URL
    response = requests.get(logo_url)

    # Open the image from the response content
    return Image.open(BytesIO(response.content))

def high_heat_filter(df: pd.DataFrame) -> pd.DataFrame:
    columns_to_keep = [
            'pitcher',
            'pitch_type',
            'pitch_name',
            'release_spin_rate', 
            'pfx_x', 'pfx_z', # HB is represented by pfx_x and iVB is represented by pfx_z
            #'estimated_woba_using_speedangle', NOTE Let's bring this back later, not great with spring training data I guess
            'release_speed'
        ]
    return df[columns_to_keep].dropna().sort_values('release_speed', ascending=False).head(5)