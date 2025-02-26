from selenium.webdriver import Chrome
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

from time import sleep
from convert_date import converter
from bs4 import BeautifulSoup as bs
import re
from dataclasses import dataclass, asdict
import json
from pprint import pprint
import warnings
import os
import sys

warnings.filterwarnings('ignore')

url_basketball = 'https://sportsbetting.dog/picks/basketball'
url_baseball = 'https://sportsbetting.dog/picks/baseball'
url_hockey = 'https://sportsbetting.dog/picks/hockey'
url_soccer = 'https://sportsbetting.dog/picks/soccer'

urls = [url_basketball, url_baseball, url_hockey, url_soccer]

@dataclass
class Item:
    sport_league: str = ''
    event_date_utc: str = ''
    team1: str = ''
    team2: str = ''
    team1_percent: str = ''
    team2_percent: str = ''
    draw_percent: str = ''
    period: str = ''
    line_type: str = ''
    price: str = ''
    side: str = ''
    team: str = ''
    spread: float = 0.0


class BettingSite:    
    def site_access(self):
        """
        Instantiates a Chrome driver with options to disable logging, suppress certificate/ssl errors, and run headlessly.
        Creates a WebDriverWait object with a 5 second timeout period.

        :return: None
        :rtype: NoneType
        """
        options = Options()
        options.add_argument('--silent')
        options.add_argument('--disable-logging')
        options.add_argument('--log-level=3')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--headless')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        self.driver = Chrome(options=options)

        self.wa = WebDriverWait(self.driver, 5)

    def parse_veri_bet(self, url: str):
        """
        Parse the given url.

        :param url: The url to be parsed. It should be one of the following urls:
            - https://sportsbetting.dog/picks/basketball
            - https://sportsbetting.dog/picks/baseball
            - https://sportsbetting.dog/picks/hockey
            - https://sportsbetting.dog/picks/soccer

        :return: A list of Item objects, which represent the parsed data.
        """
        sport = url.split('/')[-1].upper() # Get the sport name from the url

        self.driver.get(url)  # Navigate to the url

        # Wait for the page to load
        self.wa.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'card-body')))
        while True:
            card_bodys = self.driver.find_elements(By.CLASS_NAME, 'card-body')
            card = card_bodys[0]
            if 'loading' in card.text.lower():
                self.driver.execute_script("arguments[0].scrollIntoView();", card)
                continue
            else:
                break

        page_source = self.driver.page_source  # Get the page source

        soup = bs(page_source, 'html.parser')  # Parse the page source with BeautifulSoup

        # Find all the cards in the page
        cards = soup.find_all('div', {'class': 'card-body'})
        headers = soup.find_all('div', {'class': 'card-header'})

        # If there are no cards in the page, return an empty list
        if len(cards) == 0:
            item = [headers[0].text.replace('\n', '').replace('\t', '').strip()]
            return item
        else: # Otherwise, parse the cards
            card = cards[0]  # Get the first card

            rows = card.find_all('div', {'class': 'row'})  # Find all the rows in the card

            # Initialize an empty list to store the parsed data
            items = []
            row = rows[0]
            body = row.find('tbody')
            spans = body.find_all('span')

            # Verify the period of the game
            time_class = spans[0].get('class')[0]
            if time_class == 'text-danger':
                period = 'in progress'
                if spans[2].text == 'FINAL':
                    period = 'full time'
            elif time_class == 'text-info':
                period = 'soon'
            else:
                period = ''

            dados = [span.text.replace('\t', '').replace('\n', '') for span in spans]  # Get the text of the spans

            # Verify the number of elements in the list
            if len(dados) == 28 or len(dados) == 29:
                dados.pop(12)
                dados.pop(7)
                dados.pop(2)

            date = dados[0]
            event_date_utc = converter(date)  # Convert the date to UTC

            # Get the game information
            spread1 = dados[7]
            if spread1 == 'N/A':
                spread1_hand = spread1_price = spread1
            else:
                spread1_hand = float(spread1[:spread1.find('(')].strip())
                spread1_price = spread1[spread1.find('(')+1:].strip().replace(')', '')

            total1 = dados[8]
            if total1 == 'N/A':
                total1_spread = total1_price = total1
            else:
                total1_spread = total1[1:total1.find('(')].strip()
                total1_price = total1[total1.find('(')+1:].strip().replace(')', '')

            spread2 = dados[11]
            if spread2 == 'N/A':
                spread2_hand = spread2_price = spread2
            else:
                spread2_hand = float(spread2[:spread2.find('(')].strip())
                spread2_price = spread2[spread2.find('(')+1:].strip().replace(')', '')

            total2 = dados[12]
            if total2 == 'N/A':
                total2_spread = total2_price = total2
            else:
                total2_spread = total2[1:total2.find('(')].strip()
                total2_price = total2[total2.find('(')+1:].strip().replace(')', '')

            draw = dados[16].replace('DRAW', '').strip()  # Get the draw value

            percents = row.find_all('p')  # Find all the percents

            # Get the percents
            team1_wins = percents[3].text
            percent1 = team1_wins[team1_wins.find(':')+1:].strip()
            team2_wins = percents[4].text
            percent2 = team2_wins[team2_wins.find(':')+1:].strip()

            # Check if the sport is soccer
            isdraw = False
            if sport == 'SOCCER':
                team3_wins = body.find_all('p', {'class': 'text-warning'})[-1].text
                percent3 = team3_wins[team3_wins.find(':')+1:].strip()
                isdraw = True
            else:
                percent3 = ''

            team1 = {
                'name': dados[5],
                'moneyline': dados[6],
                'spread': spread1_hand,
                'spreadPrice': spread1_price,
                'totalSide': 'over',
                'totalSpread': total1_spread,
                'totalPrice': total1_price
            }

            team2 = {
                'name': dados[9],
                'moneyline': dados[10],
                'spread': spread2_hand,
                'spreadPrice': spread2_price,
                'totalSide': 'under',
                'totalSpread': total2_spread,
                'totalPrice': total2_price
            }
            
            line_types = ('moneyline', 'spread', 'over/under') # Define the line types

            if isdraw:
                teams = [team1, team2, 'draw']
            else:
                teams = [team1, team2]

            # Loop through the teams
            for line_type in line_types:
                for team in teams: 
                    try:
                        side = team_line = team['name']
                    except TypeError:
                        side = team_line = team
                    if line_type == 'moneyline':
                        if team == 'draw':
                            price = draw
                        else:
                            price = team['moneyline']
                        spread = 0
                    elif line_type == 'spread':
                        if team == 'draw':
                            continue
                        price = team['spreadPrice']
                        spread = team['spread']
                    elif line_type == 'over/under':
                        if team == 'draw':
                            continue
                        price = team['totalPrice']
                        spread = team['totalSpread']
                        side = team['totalSide']
                        team_line = 'total'

                    item = Item(
                        sport_league=sport,
                        event_date_utc=event_date_utc,
                        team1=team1['name'],
                        team2=team2['name'],
                        team1_percent=percent1,
                        team2_percent=percent2,
                        draw_percent=percent3,
                        period=period,
                        line_type=line_type,
                        price=price,
                        side=side,
                        team=team_line,
                        spread=spread,
                    )

                    items.append(item)

            # Print the items as a json object
            json_data = json.dumps([asdict(item) for item in items], indent=4)
            print(json_data+'\n')

            sleep(1)
                    
def run():
    """
    Infinite loop that parses the odds of the given urls and prints them to stdout as a json object.
    
    The json object is a dictionary where the key is the name of the sport and the value is a list of Item objects, 
    which are dictionaries with the following keys: sport_league, event_date_utc, team1, team2, team1_percent, team2_percent, draw_percent, period, line_type, price, side, team, spread.
    """
    
    betting = BettingSite()
    betting.site_access()
    while True:
        for url in urls:
            betting.parse_veri_bet(url)
        sleep(5)

if __name__=='__main__':
    run()

