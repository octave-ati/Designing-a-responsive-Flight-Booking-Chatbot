import requests
import pandas as pd
import numpy as np
import os


try :
    #If config loads, load the API key from the file
    import config  
    pred_endpoint = config.pred_endpoint
    pred_key = config.pred_key
    app_id = config.app_id

except ImportError:
    #We load the secrets from the loaded variables 
    pred_endpoint = os.environ.get("PRED_ENDPOINT")
    pred_key = os.environ.get("PRED_KEY")
    app_id = os.environ.get("LUIS_APP_ID")


relevant_entities = ['budget','dst_city','or_city','str_date','end_date']

entities_dict = {'budget': 'Budget', 'dst_city': 'Destination City', 'or_city': 'Departure City','str_date': 'Start Date',
'end_date': 'Return Date'}

def get_entities(query):

        # YOUR-APP-ID: The App ID GUID found on the www.luis.ai Application Settings page.
    appId = app_id

    # YOUR-PREDICTION-KEY: Your LUIS prediction key, 32 character value.
    prediction_key = pred_key

    # YOUR-PREDICTION-ENDPOINT: Replace with your prediction endpoint.
    # For example, "https://westus.api.cognitive.microsoft.com/"
    prediction_endpoint = pred_endpoint

    # The utterance you want to use.
    utterance = query
    ##########

    # The headers to use in this REST call.
    headers = {
    }

    # The URL parameters to use in this REST call.
    params ={
        'query': utterance,
        'timezoneOffset': '0',
        'verbose': 'true',
        'show-all-intents': 'true',
        'spellCheck': 'false',
        'staging': 'true',
        'subscription-key': prediction_key
    }


    # Make the REST call.
    response = requests.get(f'{prediction_endpoint}luis/prediction/v3.0/apps/{appId}/slots/staging/predict', headers=headers, params=params)
    
    return response.json()


def get_first(entity):
    return entity[0]

def update_entities(step_context, resp):
    entity_resp = pd.DataFrame.from_dict(resp['prediction'])[['entities']]

    entity_resp = entity_resp.loc[np.isin(entity_resp.index, relevant_entities)]

    entity_resp['entities'] = entity_resp['entities'].apply(get_first)

    #Assigning entities to context
    for index, row in entity_resp.iterrows():
        step_context.values[index] = row['entities']


    
    return entity_resp