from ..core.context import Context
from ..utils.workspace import inside_workspace


class ParadeCommand(object):
    """
    The base class to implement a sub-command in parade command line entry point
    """
    requires_workspace = False
    workspace_name = None
    workspace_path = None
    config = None

    def short_desc(self):
        """
        A short description of the command
        """
        raise NotImplementedError

    def long_desc(self):
        """A long description of the command. Return short description when not
        available. It cannot contain newlines, since contents will be formatted
        by optparser which removes newlines and wraps text.
        """
        return self.short_desc()

    def help(self):
        """An extensive help for the command. It will be shown when using the
        "help" command. It can contain newlines, since not post-formatting will
        be applied to its contents.
        """
        return self.long_desc()

    def config_parser(self, parser):
        """
        Populate option parse with options available for this command
        """
        raise NotImplementedError

    def run(self, **kwargs):
        """
        Entry point for running commands
        """
        context = None
        if self.requires_workspace:
            assert inside_workspace()
            assert 'workspace' in kwargs
            assert 'workdir' in kwargs
            assert 'config' in kwargs

            workspace = kwargs['workspace']
            workdir = kwargs['workdir']
            config = kwargs['config']
            context = Context(workspace, config, workdir=workdir)

        self.run_internal(context, **kwargs)

    def run_internal(self, context, **kwargs):
        """
        Internal running logic, to be implemented
        :param context: the context to use
        :return:
        """
        raise NotImplementedError
