from parade.cmdline import execute
class TestCmdline(object):
    def test_no_cmd(self):
        assert execute() == 0

    def test_one(self):
        assert 1 == 1
