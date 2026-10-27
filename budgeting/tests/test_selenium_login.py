"""TC_FH_01 — вхід користувача (Selenium)."""

from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class LoginSeleniumTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        opts = Options()
        opts.add_argument('--headless=new')
        opts.add_argument('--window-size=1280,900')
        cls.driver = webdriver.Chrome(options=opts)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def test_login(self):
        User.objects.create_user('demo_test', password='pass12345')
        d = self.driver
        d.get(f'{self.live_server_url}/accounts/login/')
        d.find_element(By.NAME, 'username').send_keys('demo_test')
        d.find_element(By.NAME, 'password').send_keys('pass12345')
        btn = d.find_element(By.CSS_SELECTOR, '.fh-auth-card button[type=submit]')
        d.execute_script('arguments[0].click()', btn)
        self.assertIn('/dashboard', d.current_url)
