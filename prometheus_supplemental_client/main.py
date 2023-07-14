#!/usr/bin/env python3

from prometheus_client import start_http_server, Gauge
from os import environ
from os.path import exists, expanduser
import json
import requests
import time


def find_creds():
    # creds = {}
    try:
        if all(x in environ for x in ['api_compute', 'pc_username', 'pc_password']):
            creds = {'api_compute': environ.get('api_compute'), 'username': environ.get('pc_username'), 'password': environ.get('pc_password')}
        elif exists("./credentials.json"):
            creds = json.load(open('./credentials.json'))
        elif exists("/credentials.json"):
            creds = json.load(open('/credentials.json'))
        else:
            creds = json.load(open(f"{expanduser('~')}/.prismacloud/credentials.json"))
    except:
        print("Couldn't find a set of credentials.\nIt should be in variables or one of\n~/.prismacloud/credentials.json\n./credentials.json")
    return creds


def authenticate():
    # This first condition will help us not hit the authentication API for every iteration.
    global tokenBirthtime
    if (all(x in globals() for x in ['token', 'url'])) and (time.time() - tokenBirthtime < 3600):
        print(f'Skipped Auth! {time.time() - tokenBirthtime} seconds passed.')
        return token, url
    else:

        # Tries to authenticate untill success
        succeed = False
        while not succeed:
            try:
                creds = find_creds()
                rbody = {'username': creds['username'], 'password': creds['password']}
                r = requests.post(f"{creds['api_compute']}/api/v1/authenticate", json = rbody)
                if r.status_code == 200:
                    succeed = True
                    print("New Auth")
                    tokenBirthtime = time.time()
                    response = r.json() 
                    return response['token'], creds['api_compute']
                else:
                    print(f'Auth did not succeed(status code {r.status_code}), waiting 5 min')
                    raise ValueError(f'Auth did not succeed(status code {r.status_code}), waiting 5 min')
            except:
                time.sleep(300)
                continue
 


def get_data(token, url):
    succeed = False
    while not succeed:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            r = requests.get(f"{url}/api/v1/cloud/discovery", headers=headers)
            if r.status_code == 200:
                data = r.json()
                succeed = True
                return data
            else:
                print(f"The data call did not succeed.  Code {r.status_code}")
                raise ValueError('The API call did not succeed')
        except:
            time.sleep(300)
            continue


# Create a metric to track time spent and requests made.
pcc_total_assets = Gauge('pcc_total_assets', 'Total Assets', ['credentialId','account', 'provider', 'region', 'service'])
pcc_defended_assets = Gauge('pcc_defended_assets', 'Defended Assets', ['credentialId','account', 'provider', 'region', 'service'])


if __name__ == '__main__':
    # Start up the server to expose the metrics.
    start_http_server(8000)
    while True:
        token, url = authenticate()
        data = get_data(token, url)
        for i in data:
            #below if statement helps avoid errors if there is a recently deleted account 
            if ("err" not in i and "accountID" in i):
                pcc_total_assets.labels(credentialId=i['credentialId'], account=i['accountID'], provider=i['provider'], region=i['region'], service=i['serviceType']).set(i['total'])
                pcc_defended_assets.labels(credentialId=i['credentialId'], account=i['accountID'], provider=i['provider'], region=i['region'], service=i['serviceType']).set(i['defended'])
            else:
                continue
        time.sleep(60)
