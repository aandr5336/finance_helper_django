"""TC_FH_02 — створення витрати (Selenium)."""

from time import sleep

from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from budgeting.models import Category, Transaction


class CreateExpenseSeleniumTest(StaticLiveServerTestCase):
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

    def test_create_expense(self):
        user = User.objects.create_user('book_test', password='pass12345')
        cat = Category.objects.create(owner=user, name='Food', category_type='expense')

        # логін без форми — лише cookie сесії
        self.client.force_login(user)
        self.driver.get(self.live_server_url)
        self.driver.add_cookie({'name': 'sessionid', 'value': self.client.session.session_key, 'path': '/'})

        d = self.driver
        d.get(f'{self.live_server_url}/transactions/add/')
        tx_type = d.find_element(By.NAME, 'tx_type')
        Select(tx_type).select_by_value('expense')
        d.execute_script(
            "arguments[0].dispatchEvent(new Event('change', {bubbles:true}))",
            tx_type,
        )
        # дати JS перебудувати <option> за типом
        sleep(0.3)
        Select(d.find_element(By.NAME, 'category')).select_by_value(str(cat.pk))
        d.find_element(By.NAME, 'amount').send_keys('50')
        d.find_element(By.NAME, 'note').send_keys('test')
        d.execute_script(
            'arguments[0].click()',
            d.find_element(By.CSS_SELECTOR, '#transaction-form button[type=submit]'),
        )

        self.assertTrue(Transaction.objects.filter(owner=user, note='test').exists())
