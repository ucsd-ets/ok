from server.models import db, Backup, Group, Message, GradingTask, Score
import server.utils as utils
from server import generate
from server import constants
from server.controllers import api
from server.jobs.effort import *

from itertools import zip_longest

from tests import OkTestCase

class TestEffortGrading(OkTestCase):
    """Tests Grading/Queue Generation."""
    def setUp(self):
        super().setUp()
        self.setup_course()

    def make_backup(self, grading=None, attempts=None, submit=False):
        """
        Create a Backup with specific message info.

        ``grading`` is a string where each character is a grade for a question:

            'c' - correct
            'p' - passed at least one testcase
            'f' - failed
            ' ' - omitted

        ``attempts`` is a string where each character is the number of attempts
        for a question:

            '#' - number of attempts
            ' ' - omitted

        ``submit`` where the Backup is a submission
        """
        grading = grading or ''
        attempts = attempts or ''
        messages = {
            'grading': {
                q: {
                    'failed': 0 if result == 'c' else 1,
                    'locked': 0 if result == 'c' else 1,
                    'passed': 1 if result == 'p' else 0
                }
                for q, result in enumerate(grading) if result != ' '
            },
            'analytics': {
                'history': {
                    'questions': {
                q: {
                    'solved': result == 'c',
                    'attempts': int(n) if n != ' ' else 0
                }
                for q, (result, n) in enumerate(zip_longest(grading, attempts, fillvalue=' '))
                    if not (result == ' ' and n == ' ')
                    }
                }
            }
        }
        return api.make_backup(self.user1, self.assignment.id, messages, submit)

    def score_equals(self, backup, score, qs=2):
        try:
            effort, _ = effort_score(backup, 2, qs, attempts_needed=3)
        except AssertionError:
            effort = 0
        print(effort)
        self.assertEquals(effort, score)

    def test_effort_grading(self):
        """
        Full credit if question is correct or at least one testcase passed
        """
        self.score_equals(self.make_backup(), 0)

        self.score_equals(self.make_backup(grading='cc'), 2)
        self.score_equals(self.make_backup(grading='cp'), 2)
        self.score_equals(self.make_backup(grading='pp'), 2)
        self.score_equals(self.make_backup(grading='pf'), 0)
        self.score_equals(self.make_backup(grading='p'), 0)
        self.score_equals(self.make_backup(grading=' p'), 0)

    def test_effort_attempts(self):
        """
        Full credit if question has at least three attempts
        """
        self.score_equals(self.make_backup(grading='ff', attempts='33'), 2)
        self.score_equals(self.make_backup(grading='ff', attempts='32'), 0)
        self.score_equals(self.make_backup(grading='fc', attempts='32'), 2)
        self.score_equals(self.make_backup(grading='cf', attempts='32'), 0)
        self.score_equals(self.make_backup(grading='pf', attempts='11'), 0)
        self.score_equals(self.make_backup(grading='ff', attempts='39'), 2)
        self.score_equals(self.make_backup(grading='ff', attempts='3'), 0)
        self.score_equals(self.make_backup(attempts='3'), 0)
        self.score_equals(self.make_backup(attempts='53'), 2)
        self.score_equals(self.make_backup(attempts='13'), 0)

    def test_effort_ceil(self):
        """
        Points should ceil to nearest point (no decimals)
        """
        self.score_equals(self.make_backup(grading='c'), 0, qs=3)
        self.score_equals(self.make_backup(grading='ffc'), 0, qs=3)
        self.score_equals(self.make_backup(grading='fcc'), 0, qs=3)
        self.score_equals(self.make_backup(attempts='111'), 0, qs=3)

    def test_effort_missing(self):
        self.score_equals(self.make_backup(grading='f c', attempts='33 '), 2, qs=3) # 2
        self.score_equals(self.make_backup(grading='p', attempts=' 3'), 2)

