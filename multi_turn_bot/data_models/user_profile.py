# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.schema import Attachment


class UserProfile:
    """
      This is our application state. Just a regular serializable Python class.
    """

    def __init__(self, name: str = None, transport: str = None, age: int = 0,
     picture: Attachment = None, destination: str=None, departure: str=None, budget: int=None,
     start_date: str=None, end_date: str=None):
        self.name = name
        self.transport = transport
        self.age = age
        self.picture = picture
        self.destination = destination
        self.departure = departure
        self.start_date = start_date
        self.end_date = end_date
        self.budget = budget
