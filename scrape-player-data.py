from bs4 import BeautifulSoup
import datetime as dt
import pandas as pd
import requests

team_id = 2598
season_id = 155

url = f'https://www.soccerbase.com/teams/team.sd?team_id={team_id}&teamTabs=stats&season_id={season_id}'
r = requests.get(url)
doc = BeautifulSoup(r.text, 'html.parser')

season_range = doc.select_one('#statsSeasonSelectTop')
season_list = season_range.select('option')

season_ids_to_scrape = []

for season in season_list:
    sb_season_id = season['value']
    if sb_season_id != '0':
        season_ids_to_scrape.append(sb_season_id)

all_players = []

for season_id in season_ids_to_scrape:
    url = f'https://www.soccerbase.com/teams/team.sd?team_id={team_id}&teamTabs=stats&season_id={season_id}'
    r = requests.get(url)
    doc = BeautifulSoup(r.text, 'html.parser')

    season = doc.select_one('.seasonSelector h3').text
    print(f"Scraping season {season}")

    player_list = doc.select('table.center tbody tr')
    
    for player in player_list:
        player_info = player.select_one('.first')
    
        player_name = player_info.get_text()
        player_name = player_name.split('(')
        player_name = player_name[0]
        player_name = player_name.strip()
    
        sb_player_id = player_info.select_one('a')['href']
        sb_player_id = sb_player_id.split('=')[1]
    
        # Next step is scrape the games this played in during this season
        # Construct a url to bring up the player's record for that season
        player_season_url = f'https://www.soccerbase.com/players/player.sd?player_id={sb_player_id}&season_id={season_id}'

        r = requests.get(player_season_url)
        doc = BeautifulSoup(r.text, 'html.parser')
    
        games_played = doc.select('.soccerGrid .match')
        
        for game in games_played:
            # Checking that the record isn't about the player playing AGAINST Tranmere
            home_team = game.select_one('.homeTeam').text
            away_team = game.select_one('.awayTeam').text
            
            opposition_team = game.select_one('.inactive').text

            sb_opposition_id = game.select_one('.inactive a')['href']
            sb_opposition_id = sb_opposition_id.split('=')
            sb_opposition_id = sb_opposition_id[1]

            if ('Tranmere' not in [home_team, away_team]) or (opposition_team == 'Tranmere'):
                next
            else:
                sb_game_id = game['id']
                
                competition = game.select_one('.tournament')
                try:
                    competition_text = competition.select_one('a').text
                except:
                    competition_text = competition.text.strip()
                
                try:
                    sb_competition_id = competition.select_one('a')['href']
                    sb_competition_id = sb_competition_id.split('=')
                    sb_competition_id = sb_competition_id[1]
                except:
                    sb_competition_id = 'N/A'
                
                game_date = game.select_one('.dateTime a')['href']
                game_date = game_date.split('=')[1]
                game_date = dt.datetime.strptime(game_date, "%Y-%m-%d")

                score = game.select_one('.score')
                score = score.select('em')                
                
                if home_team == 'Tranmere':
                    venue = 'H'
                    goals_for = score[0].text
                    goals_for = int(goals_for)
                    goals_against = score[1].text
                    goals_against = int(goals_against)
                else:
                    venue = 'A'
                    goals_for = score[1].text
                    goals_for = int(goals_for)
                    goals_against = score[0].text
                    goals_against = int(goals_against)
                    
                goals_and_cards = game.select('.blankCard')
                pl_goals = goals_and_cards[0].text
                if pl_goals == '':
                    pl_goals = 0
                else:
                    pl_goals = int(pl_goals)
                    
                yellow_card = goals_and_cards[1]
                yellow_card = bool(yellow_card.select_one('img'))
                if yellow_card:
                    yellow_card = 1
                else:
                    yellow_card = 0
                
                red_card = goals_and_cards[2]
                red_card = bool(red_card.select_one('img'))
                if red_card:
                    red_card = 1
                else:
                    red_card = 0

                player_record = [season,
                                 season_id,
                                 sb_player_id,
                                 player_name,
                                 sb_opposition_id,
                                 opposition_team,
                                 sb_game_id,
                                 sb_competition_id,
                                 competition_text,
                                 venue,
                                 game_date,
                                 goals_for,
                                 goals_against,
                                 pl_goals,
                                 yellow_card,
                                 red_card
                ]
                
                all_players.append(player_record)

        print(f'Scraped {season}: {player_name}')

df = pd.DataFrame(all_players, columns = ['season',
                                 'season_id',
                                 'sb_player_id',
                                 'player_name',
                                 'sb_opposition_id',
                                 'opposition_team',
                                 'sb_game_id',
                                 'sb_competition_id',
                                 'competition_text',
                                 'venue',
                                 'game_date',
                                 'goals_for',
                                 'goals_against',
                                 'pl_goals',
                                 'yellow_cards',
                                 'red_cards'])

df.to_csv('./data/players_df.csv', index = False)