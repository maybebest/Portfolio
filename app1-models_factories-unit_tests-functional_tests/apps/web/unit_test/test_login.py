import json
from django.test import TestCase
from django.contrib.auth import get_user_model
# from bs4 import BeautifulSoup
from django.test import Client


class TestAdmin(TestCase):

    def setUp(self):
        self.c = Client()
        User = get_user_model()
        user = User.objects.create(email='admin@example.com')
        user.set_password('admin')
        user.is_active = True
        user.is_superuser = False
        user.role = User.APP_USER
        user.save()
        #self.c.login(email='admin@example.com', password='admin')

    def test_login_page_up(self):
        response_code_login_page = self.c.get('/login/').status_code
        self.assertEqual(response_code_login_page, 200)

    def test_login_action_correct(self):
        response_code_login_success_by_code = self.c.post('/login/', {
            'email': 'admin@example.com', 'password': 'admin'}).status_code
        self.assertEqual(response_code_login_success_by_code, 200)

        response_code_login_success = self.c.post('/api/login/', {
            'email': 'admin@example.com', 'password': 'admin'}, **{
            'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        response_dict = json.loads(response_code_login_success.content)

        self.assertIn('success', response_dict)
        self.assertTrue(response_dict['success'])

        self.assertIn('user', response_dict)
        self.assertIn('email', response_dict['user'])
        self.assertEqual(response_dict['user']['email'], 'admin@example.com')

    def test_login_action_incorrect_email(self):
        response_code_login_bad_email = self.c.post('/api/login/', {
            'email': 'admin@example.com1', 'password': 'admin'}, **{
            'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})

        self.assertDictEqual(json.loads(response_code_login_bad_email.content), {
            "errors": "Incorrect username or password. If you are a first time user please click back and Sign Up to register.", "success": False})

    def test_login_action_incorrect_pass(self):
        response_code_login_bad_pass = self.c.post('/api/login/', {
            'email': 'admin@example.com', 'password': 'admin1'}, **{
            'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})

        self.assertDictEqual(json.loads(response_code_login_bad_pass.content), {
            "errors": "Incorrect username or password. If you are a first time user please click back and Sign Up to register.", "success": False})

    def test_login_action_no_email(self):
        response_code_login_no_email = self.c.post('/api/login/', {
            'password': 'admin1'}, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        response_dict = json.loads(response_code_login_no_email.content)

        self.assertIn('success', response_dict)
        self.assertFalse(response_dict['success'])

        self.assertIn('errors', response_dict)
        self.assertIn('email', response_dict['errors'])
        self.assertEqual(len(response_dict['errors']['email']), 1)
        self.assertEqual(response_dict['errors']['email'][0], 'This field is required.')

    def test_login_action_no_pass(self):
        response_code_login_no_pass = self.c.post('/api/login/', {
            'email': 'admin@example.com'}, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        response_dict = json.loads(response_code_login_no_pass.content)

        self.assertIn('success', response_dict)
        self.assertFalse(response_dict['success'])

        self.assertIn('errors', response_dict)
        self.assertIn('password', response_dict['errors'])
        self.assertEqual(len(response_dict['errors']['password']), 1)
        self.assertEqual(response_dict['errors']['password'][0], 'This field is required.')

