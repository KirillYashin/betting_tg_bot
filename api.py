import requests
import datetime
from bs4 import BeautifulSoup
from python_utils import converters


def get_parsed_page(url):
    headers = {
        'referer': 'https://www.hltv.org',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }

    return BeautifulSoup(requests.get(url, headers=headers).text, 'lxml')


def get_matches(event_id):
    matches = get_parsed_page('https://www.hltv.org/events/' + str(event_id) + '/matches')

    matches_list = []

    match_days = matches.find_all('div', {'class': 'upcomingMatchesSection'})

    for match in match_days:
        match_details = match.find_all('div', {'class': 'upcomingMatch'})
        date = match.find({'span': {'class': 'matchDayHeadline'}}).text.split()[-1]

        for getMatch in match_details:
            match_obj = dict()
            link = getMatch.find('a').get('href')
            match_obj['status'] = 'not live'
            match_obj['link'] = 'https://www.hltv.org' + link
            match_id = link.split('/')[2]
            match_obj['id'] = match_id
            match_obj['date'] = date
            match_obj['time'] = getMatch.find('div', {'class': 'matchTime'}).text

            if getMatch.find('div', {'class': 'matchEvent'}):
                match_obj['event'] = getMatch.find('div', {'class': 'matchEvent'}).text.strip()
            else:
                match_obj['event'] = getMatch.find('div', {'class': 'matchInfoEmpty'}).text.strip()

            if getMatch.find_all('div', {'class': 'matchTeams'}):
                match_obj['team1'] = getMatch.find_all('div', {'class': 'matchTeam'})[0].text.strip().split('\n')[0]
                match_obj['team2'] = getMatch.find_all('div', {'class': 'matchTeam'})[1].text.strip().split('\n')[0]
            else:
                match_obj['team1'] = None
                match_obj['team2'] = None

            matches_list.append(match_obj)

    return matches_list


def get_live_matches(event_id):
    matches = get_parsed_page('https://www.hltv.org/events/' + str(event_id) + '/matches')
    matches_list = []

    live_matches = matches.find_all('div', {'class': 'liveMatchesSection'})

    for match in live_matches:
        match_details = match.find_all('div', {'class': 'liveMatch'})

        for getMatch in match_details:
            match_obj = dict()
            link = getMatch.find('a').get('href')
            match_obj['status'] = 'live'
            match_obj['link'] = 'https://www.hltv.org' + link
            match_id = link.split('/')[2]
            match_obj['id'] = match_id

            match_obj['team1'] = getMatch.find_all('div', {'class': 'matchTeam'})[0].text.strip().split('\n')[0]
            match_obj['team2'] = getMatch.find_all('div', {'class': 'matchTeam'})[1].text.strip().split('\n')[0]

            matches_list.append(match_obj)

    return matches_list


def get_results(event_id):
    results = get_parsed_page('https://www.hltv.org/results?event=' + str(event_id))

    results_list = {}

    past_results = results.find_all('div', {'class': 'results-holder'})

    for result in past_results:
        result_div = result.find_all('div', {'class': 'result-con'})

        for res in result_div:
            result_obj = dict()

            link = res.find('a').get('href')
            result_obj['link'] = 'https://www.hltv.org' + link

            if res.parent.find('span', {'class': 'standard-headline'}):
                result_obj['date'] = res.parent.find('span', {'class': 'standard-headline'}).text
            else:
                dt = datetime.date.today()
                result_obj['date'] = str(dt.day) + '/' + str(dt.month) + '/' + str(dt.year)

            if res.find_all('td', {'class': 'team-cell'}):
                result_obj['team1'] = res.find_all('td', {'class': 'team-cell'})[0].text.strip()
                result_obj['team1score'] = \
                    converters.to_int(res.find('td', {'class': 'result-score'}).find_all('span')[0].text.strip())
                result_obj['team2'] = res.find_all('td', {'class': 'team-cell'})[1].text.strip()
                result_obj['team2score'] = \
                    converters.to_int(res.find('td', {'class': 'result-score'}).find_all('span')[1].text.strip())

                if result_obj['team1score'] > result_obj['team2score']:
                    result_obj['winner'] = result_obj['team1']
                else:
                    result_obj['winner'] = result_obj['team2']
            else:
                result_obj['team1'] = None
                result_obj['team2'] = None

            results_list[result_obj['team1'] + ' - ' + result_obj['team2']] = result_obj

    return results_list


def get_coefficients(link):
    match_info = get_parsed_page(link)
    odds = dict()
    coefficients_info = match_info.find_all('div', {'class': 'three-quarter-width'})

    if coefficients_info:
        odds['team1'] = match_info.find_all('td', {'class': 'team-cell'})[-2].text
        odds['team2'] = match_info.find_all('td', {'class': 'team-cell'})[-1].text
        coefficients = match_info.find_all('tr', {'class': 'provider'})[-1]
        if not coefficients.find('td', {'class': 'noOdds'}):
            c = coefficients.find_all('td', {'class': 'odds-cell border-left'})
            odds['c1'] = c[0].text
            odds['c2'] = c[1].text
        else:
            odds['c1'] = None
            odds['c2'] = None

        return odds
    else:
        return None
