import unittest
from app import app
from models import db

class APITestCase(unittest.TestCase):
    def setUp(self):
        # app.config['TESTING'] = True
        # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # ใช้ DB ชั่วคราว
        self.client = app.test_client()

        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_get_available_robots(self):
        response = self.client.get('/robots/available')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)

    def test_post_destination(self):
        data = {
            "name": "TestPlace",
            "x": 123,
            "y": 456,
            "official_name": "TestZone"
        }
        response = self.client.put('/destination', json=data)
        self.assertIn(response.status_code, [200, 201])

if __name__ == '__main__':
    unittest.main()
