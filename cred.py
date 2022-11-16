from azure.core.credentials import AzureKeyCredential
from azure.ai.language.conversations import ConversationAnalysisClient

endpoint = "https://project10.cognitiveservices.azure.com/"
credential = AzureKeyCredential("935cefcf72424b8980cf3366d5bdb1cb")
luis_key = "3db46c75177647f498d2b64fe4ba05d1"
luis_endpoint = "https://pro10.cognitiveservices.azure.com/"
client = ConversationAnalysisClient(endpoint, credential)
project_name = "LUIS"
deployment_name = "LUIS"
luis_app_id = "abb9267a-7180-4658-93ac-7d0c5e4389c3"
luis_app_version = "0.1"