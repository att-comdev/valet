# -*- encoding: utf-8 -*-
#
# Copyright (c) 2014-2016 AT&T
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pecan.commands.base import BaseCommand
from pecan import conf

from allegro import models
from allegro.models import Group
from allegro.models import Placement
from allegro.models import Plan
from allegro.models import Event
from allegro.models import PlacementRequest
from allegro.models import PlacementResult


def out(string):
    print "==> %s" % string


class PopulateCommand(BaseCommand):
    """
    Load a pecan environment and initializate the database.
    """

    def run(self, args):
        super(PopulateCommand, self).run(args)
        out("LOADING ENVIRONMENT")
        self.load_app()
        out("BUILDING SCHEMA")
        try:
            out("STARTING A TRANSACTION...")
            models.start()
            #models.Base.metadata.create_all(conf.sqlalchemy.engine)

            # Allegro
            Group.create_table()
            Placement.create_table()
            Plan.create_table()

            # Ostro
            Event.create_table()
            PlacementRequest.create_table()
            PlacementResult.create_table()
        except:
            models.rollback()
            out("ROLLING BACK... ")
            raise
        else:
            out("COMMITING... ")
            models.commit()
