import requests

def get_batter_splits(batter_id):
    url = f"https://statsapi.mlb.com/api/v1/people/{batter_id}/stats?stats=season&group=hitting&season=2025"
    response = requests.get(url)
    data = response.json()

    splits = {'vs_lhp_avg': 0.250, 'vs_rhp_avg': 0.250}
    try:
        for split in data['stats'][0]['splits']:
            code = split.get('split', {}).get('code')
            if code == 'vsL':
                splits['vs_lhp_avg'] = float(split['stat']['avg'])
            elif code == 'vsR':
                splits['vs_rhp_avg'] = float(split['stat']['avg'])
    except (KeyError, IndexError, ValueError):
        pass

    return splits