import pybaseball
import pandas as pd

pybaseball.cache.enable()


'''
start_dt, end_dt -> Date given by YYYY-MM-DD
pitcher -> First, last of pitcher (eg. Paul Skenes, Tarik Skubal, Huascar Brazoban) really tried to sneak in skubal there
'''
def fetch_pitch_data(start_dt: str, pitcher: str, end_dt: str | None = None) -> pd.DataFrame:
    
    try:
        first, last = pitcher.split(" ")

        # Fuzzy search so special chars in names dont give us a hard time
        player_id = pybaseball.playerid_lookup(last, first, fuzzy=True)['key_mlbam'].head(1).item() 
        
        if not end_dt:
            end_dt = start_dt

        daily_stats = pybaseball.statcast_pitcher(start_dt=start_dt, end_dt=end_dt, player_id=player_id)

        return daily_stats
    except:
        raise RuntimeError