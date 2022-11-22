import pytest
import insights
import config
import logging
import luis
import pandas as pd
import numpy as np
from opencensus.ext.azure.log_exporter import AzureLogHandler

#Verify that logger connection is working

wrong_instrument_key = "InstrumentationKey=811;IngestionEndpoint=https://westeurope-4.in.applicationinsights.azure.com/;LiveEndpoint=https://westeurope.livediagnostics.monitor.azure.com/"
relevant_entities = luis.relevant_entities

def configure_logger(key):
	logger = logging.getLogger(__name__)

	logger.addHandler(AzureLogHandler(
	    connection_string=key)
	)
	return logger

def test_instrument_key():
	key = config.insights_connection_string

	assert configure_logger(key)

def test_wrong_key():
	with pytest.raises(ValueError):
		configure_logger(wrong_instrument_key)

def test_luis_query():
	resp = luis.get_entities("I want to fly from Paris to Tokyo with a max budget of 123$")

	entity_resp = pd.DataFrame.from_dict(resp['prediction'])[['entities']]

	entity_resp = entity_resp.loc[np.isin(entity_resp.index, relevant_entities)]
	entity_resp['entities'] = entity_resp['entities'].apply(luis.get_first)

	assert entity_resp.to_dict()['entities']['or_city'] == "Paris"
	assert entity_resp.to_dict()['entities']['dst_city'] == "Tokyo"
	assert entity_resp.to_dict()['entities']['budget'] == "123$"


    