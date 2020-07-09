import requests

# main() will be invoked when you invoke this cloudfunction action.
def main(params):
    url = params['url']
    headers = {'accept': 'application/json'}
    r = requests.post(url,headers=headers,json=params)
    if r.status_code != 200:
        return {
            'statusCode': r.status_code,
            'headers': { 'Content-Type': 'application/json'},
            'body': {'message': 'Error procesisng your request'}
        }
    else:
        return r.json()