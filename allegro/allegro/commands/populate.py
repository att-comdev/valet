from pecan.commands.base import BaseCommand
from pecan import conf

from allegro import models


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
        models.init_model()
        out("BUILDING SCHEMA")
        try:
            out("STARTING A TRANSACTION...")
            models.start()
            models.Base.metadata.create_all(conf.sqlalchemy.engine)
        except:
            models.rollback()
            out("ROLLING BACK... ")
            raise
        else:
            out("COMMITING... ")
            models.commit()
