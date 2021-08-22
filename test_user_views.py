"""User View tests."""

import os
from unittest import TestCase

from werkzeug import test

from models import db, connect_db, Message, User, bcrypt, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False
app.config["TESTING"] = True
app.config["DEBUG_TB_HOSTS"] = ["dont-show-debug-toolbar"]

class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password=bcrypt.generate_password_hash("testuser").decode("utf-8"),
                                    image_url=None)
        db.session.add(testuser)
        db.session.commit()
        self.testuser = testuser
    
    def tearDown(self):
        """clean up the session"""

        db.session.rollback()
    
    def test_users(self):
        resp = self.client.get("/users")

        self.assertEqual(resp.status_code, 200)
        self.assertIn("testuser", str(resp.data))
    
    def test_users_show(self):
        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.testuser.id

        resp = self.client.get(f"/users/{self.testuser.id}")

        self.assertEqual(resp.status_code, 200)
        self.assertIn("@testuser", str(resp.data))
        self.assertIn("Edit Profile", str(resp.data))
    
    def test_users_show_not_signed_in(self):
        resp = self.client.get(f"/users/{self.testuser.id}")

        self.assertEqual(resp.status_code, 200)
        self.assertIn("@testuser", str(resp.data))
        self.assertNotIn("Edit Profile", str(resp.data))
    
    def test_show_following(self):
        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.testuser.id

        resp = self.client.get(f"/users/{self.testuser.id}/following")

        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("@bobby", str(resp.data))

        u = User.signup("bobby", "cat@pop.com", bcrypt.generate_password_hash("sakjg54").decode("utf-8"), None)
        db.session.add(u)
        db.session.commit()
        follow = Follows(user_being_followed_id=u.id, user_following_id=self.testuser.id)
        db.session.add(follow)
        db.session.commit()
        resp = self.client.get(f"/users/{self.testuser.id}/following")

        self.assertEqual(resp.status_code, 200)
        self.assertIn("@bobby", str(resp.data))
    
    def test_show_following_not_logged_in(self):
        resp = self.client.get(f"/users/{self.testuser.id}/following")

        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(f"/users/{self.testuser.id}/following", follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Access unauthorized.", str(resp.data))
    
    def test_show_following_user_not_exist(self):
        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.testuser.id

        resp = self.client.get("/users/-1/following")

        self.assertEqual(resp.status_code, 404)

    def test_delete_user_not_logged_in(self):
        resp = self.client.post("/users/delete")

        self.assertEqual(resp.status_code, 302)

        resp = self.client.post("/users/delete", follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Access unauthorized.", str(resp.data))

    def test_delete_user(self):
        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = self.testuser.id
        
        resp = self.client.post("/users/delete", follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(User.query.filter_by(id=self.testuser.id).one_or_none())
