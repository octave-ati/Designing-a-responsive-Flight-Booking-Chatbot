# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.schema import Attachment


class UserProfile:
    """
      This is our application state. Just a regular serializable Python class.
    """

    def __init__(self, n_entities: int=None, dst_city: str=None, or_city: str=None, budget: int=None,
     str_date: str=None, end_date: str=None):

        self.n_entities = n_entities
        self.dst_city = dst_city
        self.or_city = or_city
        self.str_date = str_date
        self.end_date = end_date
        self.budget = budget
