"""message model tests"""

import os
from unittest import TestCase
from psycopg2.errors import NotNullViolation
from sqlalchemy.exc import IntegrityError

from models import db, User, Message, Follows, Likes, bcrypt

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

app.config["TESTING"] = True
app.config["DEBUG_TB_HOSTS"] = ["dont-show-debug-toolbar"]

class MessageModelTestCase(TestCase):
    """Test views for messages"""

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

        test_message = Message(text="hello!", user_id=test_user.id)

        db.session.add(test_message)
        db.session.commit()
        
        self.user = test_user
        self.message = test_message
        self.client = app.test_client()
    
    def tearDown(self):
        """clean up the session"""

        db.session.rollback()
    
    def test_message_attributes(self):
        """Does the basic model work?"""

        m = Message(text="example", user_id=self.user.id)
        db.session.add(m)
        db.session.commit()

        self.assertEqual(m.text, "example")
    
    def test_message_ownership(self):
        """Does the message have a user?"""

        self.assertEqual(self.user.id, self.message.user_id)
        self.assertEqual(len(self.user.messages), 1)

        m = Message(text="example", user_id=self.user.id)
        db.session.add(m)
        db.session.commit()

        self.assertEqual(self.user.id, m.user_id)
        self.assertEqual(len(self.user.messages), 2)
    
    def test_message_no_user(self):
        """Does the message fail without a user?"""

        m = Message(text="no user")
        db.session.add(m)

        self.assertRaises((IntegrityError, NotNullViolation), db.session.commit)
    
    def test_message_wrong_user_id(self):
        """Does the message fail without a user?"""

        m = Message(text="user doesn't exist", user_id=-1)
        db.session.add(m)

        self.assertRaises((IntegrityError, NotNullViolation), db.session.commit)
    