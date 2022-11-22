 # Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.dialogs import (
    ComponentDialog,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
)
from botbuilder.dialogs.prompts import (
    TextPrompt,
    NumberPrompt,
    ChoicePrompt,
    ConfirmPrompt,
    AttachmentPrompt,
    PromptOptions,
    PromptValidatorContext,
)
from botbuilder.dialogs.choices import Choice
from botbuilder.core import MessageFactory, UserState

from data_models import UserProfile

import os
import luis
import pandas as pd
import insights

entities_dict = luis.entities_dict
relevant_entities = luis.relevant_entities

#Configuring logger

logger = insights.configure_logger()


def is_information_complete(step_context):
    i = 0
    for ent in relevant_entities:
        if step_context.values[ent] != None:
            i+=1

    if i > 0:
        return False
    else:
        return True


class UserProfileDialog(ComponentDialog):
    def __init__(self, user_state: UserState):
        super(UserProfileDialog, self).__init__(UserProfileDialog.__name__)

        self.user_profile_accessor = user_state.create_property("UserProfile")

        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self.initial_step,
                    self.confirm_step,
                    self.correction_step,
                    self.second_request_step,
                    self.second_confirm_step,
                    self.second_correction_step,
                    self.destination_step,
                    self.origin_step,
                    self.start_date_step,
                    self.end_date_step,
                    self.budget_step,
                    self.summary_step,
                    self.rating_step,
                ],
            )
        )
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(TextPrompt("prompt:validation"))
        self.add_dialog(
            NumberPrompt(NumberPrompt.__name__, UserProfileDialog.age_prompt_validator)
        )
        self.add_dialog(ChoicePrompt(ChoicePrompt.__name__))
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        self.add_dialog(
            AttachmentPrompt(
                AttachmentPrompt.__name__, UserProfileDialog.picture_prompt_validator
            )
        )

        self.initial_dialog_id = WaterfallDialog.__name__

    async def initial_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        # WaterfallStep always finishes with the end of the Waterfall or with another dialog;
        # here it is a Prompt Dialog. Running a prompt here means the next WaterfallStep will
        # be run when the users response is received.
        #Setting step_context values to None
        for ent in relevant_entities:
            step_context.values[ent] = None


        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text(
                    "Welcome to FlyBot! Please tell me where you want to fly, your departure location, starting and return dates and budget")),
        )
    async def confirm_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:

        resp = luis.get_entities(step_context.result)
        entities = luis.update_entities(step_context, resp)

        #Generating pre generated entities to prevent repetitive API requests
        # entities = pd.DataFrame([{'entities': 'Toronto'}, {'entities': 'Budapest'},
        #     {'entities': 'November 11th'}], index=['or_city','dst_city','str_date'])
        # step_context.values['or_city'] = 'Toronto'
        # step_context.values['dst_city'] = 'Budapest'
        # step_context.values['str_date'] = 'November 11th'

        if len(entities) == 0 :
            await step_context.context.send_activity(MessageFactory.text(
                "No booking information detected, please try again."))
            error_properties = {'custom_dimensions': {'query': resp['query']}}
            logger.error("No Prediction", extra = error_properties)

            return await step_context.next(-99)




        return_msg = "Here is the retrieved information: \r\n"
        for index, row in entities.iterrows():
            return_msg += entities_dict[index] + " : " + row['entities'] + " \r\n"



        await step_context.context.send_activity(MessageFactory.text(return_msg))

        return await step_context.prompt(
            ConfirmPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("Do you confirm the information above?")
            ),
        )
    

    async def correction_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:

       if step_context.result == -99:
        insights.save_success_data(success=False)
        return await step_context.next(-1) 
      
       elif step_context.result:
        insights.save_success_data(success=True)
        return await step_context.next(-1)

       else:
            insights.save_success_data(success=False)
            choices = []
            for ent in relevant_entities:
                if step_context.values[ent] != None:

                    choices.append(Choice(entities_dict[ent]))
            return await step_context.prompt(
            ChoicePrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("Please select wrongly detected information:"),
                choices=choices,
            ),)

    async def second_request_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        
        if step_context.result != -1:

            step_context.values[step_context.result] = None
            await step_context.context.send_activity(MessageFactory.text(
                "Thank you for your help! Clearing wrong information."))

        elif is_information_complete(step_context):
            return await step_context.next(-5)


        text = "Please provide me with the information below so I can complete your flight booking: \r \n"
        for ent in relevant_entities:
                if step_context.values[ent] == None:
                    text += entities_dict[ent] + "\r \n"
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text(
                    text)),
        )
    async def second_confirm_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:

        if step_context.result == -5:
            return await step_context.next(-5)

        # resp = luis.get_entities(step_context.result)
        # entities = luis.update_entities(step_context, resp)

        #Generating pre generated entities to prevent repetitive API requests
        entities = pd.DataFrame([{'entities': '2500$'}], index=['budget'])

        if len(entities) == 0 :
            await step_context.context.send_activity(MessageFactory.text(
                "No booking information detected, switching to manual input."))

            #Logging error
            error_properties = {'custom_dimensions': {'query': resp['query']}}
            logger.error("No Prediction", extra = error_properties)

            return await step_context.next(-99)

        #Logging request results
        properties = {'custom_dimensions': {**{'query': resp['query']}, **entities.to_dict()['entities']}}
        logger.info("Predicted Information", extra= properties )

        step_context.values['budget'] = '2500$'

        return_msg = "Here is the retrieved information: \r\n"
        for index, row in entities.iterrows():
            return_msg += entities_dict[index] + " : " + row['entities'] + " \r\n"

        await step_context.context.send_activity(MessageFactory.text(return_msg))

        return await step_context.prompt(
            ConfirmPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("Do you confirm the information above?")
            ),
        )



    async def second_correction_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
       # step_context.values["transport"] = step_context.result
       if step_context.result == -5:
            return await step_context.next(-5)
        
       elif step_context.result == -99:
            insights.save_success_data(success=False)
            return await step_context.next(-1)

       elif step_context.result:
        insights.save_success_data(success=True)
        return await step_context.next(-1)

       else:
            insights.save_success_data(success=False)
            choices = []
            for ent in relevant_entities:
                if step_context.values[ent] != None:

                    choices.append(Choice(ent))
            return await step_context.prompt(
            ChoicePrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("Please select wrongly detected information:"),
                choices=choices,
            ),)


    async def destination_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        
        if step_context.result == -5 :
            return await step_context.next(-5)

        elif step_context.result != -1:

            step_context.values[step_context.result] = None
            await step_context.context.send_activity(MessageFactory.text(
                "Thank you for your help! Clearing wrong information."))

        elif is_information_complete(step_context):
            return await step_context.next(-5)

        await step_context.context.send_activity(MessageFactory.text(
                "Unable to retrieve all necessary information."))

        if step_context.values['dst_city'] != None:
            return await step_context.next(-1)

        else:

            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("Please tell me with your destination city")),
            )

    async def origin_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if step_context.result == -5 :
            return await step_context.next(-5)
        elif step_context.result != -1:

            await step_context.context.send_activity(MessageFactory.text(
                f"Your destination is {step_context.result}"))
            step_context.values['dst_city'] = step_context.result

        if is_information_complete(step_context):
            return await step_context.next(-5)

        elif step_context.values['or_city'] != None:
            return await step_context.next(-1)

        else:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("Please tell me your departure city")),
            )

    async def start_date_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if step_context.result == -5 :
            return await step_context.next(-5)
        elif step_context.result != -1:

            await step_context.context.send_activity(MessageFactory.text(
                f"Your departure city is {step_context.result}"))
            step_context.values['or_city'] = step_context.result

        if is_information_complete(step_context):
            return await step_context.next(-5)

        elif step_context.values['str_date'] != None:
            return await step_context.next(-1)
            
        else:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("Please tell me your desired departure date")),
            )

    async def end_date_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if step_context.result == -5 :
            return await step_context.next(-5)
        elif step_context.result != -1:

            await step_context.context.send_activity(MessageFactory.text(
                f"Your departure date is {step_context.result}"))
            step_context.values['str_date'] = step_context.result

        if is_information_complete(step_context):
            return await step_context.next(-5)

        elif step_context.values['end_date'] != None:
            return await step_context.next(-1)
            
        else:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("Please tell me your desired return date")),
            )

    async def budget_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if step_context.result == -5 :
            return await step_context.next(-5)
        elif step_context.result != -1:

            await step_context.context.send_activity(MessageFactory.text(
                f"Your return date is {step_context.result}"))
            step_context.values['end_date'] = step_context.result

        if is_information_complete(step_context):
            return await step_context.next(-5)

        elif step_context.values['budget'] != None:
            return await step_context.next(-1)
            
        else:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("Please tell me your maximum budget")),
            )


    async def summary_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:

        if (step_context.result != -5) & (step_context.result != -1):
            await step_context.context.send_activity(MessageFactory.text(
                f"Your maximum budget is {step_context.result}"))
            step_context.values['budget'] = step_context.result  


        if step_context.result:
            # Get the current profile object from user state.  Changes to it
            # will saved during Bot.on_turn.
            user_profile = await self.user_profile_accessor.get(
                step_context.context, UserProfile
            )

            user_profile.budget = step_context.values['budget']
            user_profile.str_date = step_context.values['str_date']
            user_profile.end_date = step_context.values['end_date']
            user_profile.or_city = step_context.values['or_city']
            user_profile.dst_city = step_context.values['dst_city']

            return_msg = "Thank you for using this bot. Please find below the information for this booking : \r \n"

            for ent in relevant_entities:
                return_msg += entities_dict[ent] + " : " + step_context.values[ent] + " \r\n"

            await step_context.context.send_activity(MessageFactory.text(return_msg))

            await step_context.context.send_activity(MessageFactory.text(
                "Thank you for using Flybot. \r \n Your flight details will be send to you by mail shortly"))

            return await step_context.prompt(
            ChoicePrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("Please rate this bot:"),
                choices=[Choice("1"), Choice("2"),Choice("3"), Choice("4"), Choice("5")],
            ),)

        # WaterfallStep always finishes with the end of the Waterfall or with another
        # dialog, here it is the end.
        return await step_context.end_dialog()

    async def rating_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        
        score = int(step_context.result)

        insights.save_user_score(score)

        await step_context.context.send_activity(MessageFactory.text(
                "Thank you for your help in improving this bot! Have a wonderful day!"))
        return await step_context.end_dialog()        

    @staticmethod
    async def age_prompt_validator(prompt_context: PromptValidatorContext) -> bool:
        # This condition is our validation rule. You can also change the value at this point.
        return (
            prompt_context.recognized.succeeded
            and 0 < prompt_context.recognized.value < 150
        )