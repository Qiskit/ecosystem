"""
Validator base classes
"""

# pylint: disable=keyword-arg-before-vararg, invalid-name)


class MemberValidator:
    """Base-class for members"""

    def __init__(self):
        self.valid = None
        self.reason = None
        self.member = None

    def test(self):
        """Implement this method to test a validation"""
        raise NotImplementedError("")

    def validate(self, member):
        """Main entry point for a MemberValidator"""
        self.member = member
        self.test()

    def assertIn(self, item, container, msg=None, *args):
        """Checks if item is in container"""
        if item in container:
            self.valid = True
        else:
            self.reason = f"{self.member.name_id}: "
            if msg:
                self.reason = msg.format(*args)
            else:
                self.reason += f"{item} missing from container"
            self.valid = False
            raise AssertionError(self.reason)

    def assertSubset(self, small_set, big_set, msg=None, *args):
        """Checks if all the elemnts in small_set are in big_set"""
        missing = []
        self.valid = True
        for item_in_small in small_set:
            if item_in_small not in big_set:
                missing.append(item_in_small)
                self.valid = False
        if not self.valid:
            self.reason = f"{self.member.name_id}: "
            if msg:
                self.reason += msg.format(*args)
            else:
                self.reason += f"{missing} missing from set"
            raise AssertionError(self.reason)
