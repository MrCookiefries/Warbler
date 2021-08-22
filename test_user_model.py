"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError

from models import db, User, Message, Follows, Likes, bcrypt

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

app.config["TESTING"] = True
app.config["DEBUG_TB_HOSTS"] = ["dont-show-debug-toolbar"]

class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        test_user = User(
            email="something@test.com",
            username="somebody",
            password=bcrypt.generate_password_hash("protected").decode("utf-8")
        )

        db.session.add(test_user)
        db.session.commit()
        
        self.user = test_user
        self.client = app.test_client()
    
    def tearDown(self):
        """clean up the session"""

        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers & no likes
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(len(u.likes), 0)
    
    def test_user_repr(self):
        """does the repr method work right?"""

        u = self.user
        repr = u.__repr__()
        
        self.assertIn(str(u.id), repr)
        self.assertIn(u.username, repr)
        self.assertIn(u.email, repr)
    
    def test_is_following(self):
        """does the is_following method work right?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        self.assertFalse(self.user.is_following(u))

        self.user.following.append(u)

        self.assertTrue(self.user.is_following(u))
    
    def test_is_followed_by(self):
        """does this method work right?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        self.assertFalse(self.user.is_followed_by(u))

        self.user.followers.append(u)

        self.assertTrue(self.user.is_followed_by(u))
    
    def test_signup(self):
        """does this classmethod work right?"""

        user = User.signup("somebody", "bruh@gmail.com", "thisishard@234", "")
        self.assertIsInstance(user, User)
        self.assertRaises((UniqueViolation, IntegrityError), db.session.commit)

    def test_authenticate(self):
        """does the method work for many cases?"""

        user = User.authenticate("somebody", "protected")

        self.assertTrue(user)
        self.assertIsInstance(user, User)
        self.assertEqual(user.id, self.user.id)
        self.assertFalse(User.authenticate("nobody", "protected"))
        self.assertFalse(User.authenticate("somebody", "notprotected"))
