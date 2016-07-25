from django.test import TestCase
from .models import Store, MenuItem

# Create your tests here.

class HomeViewTests(TestCase):
    def setUp(self):
        Store.objects.create(name='肯德基', notes='薄皮嫩雞')
        mcdonalds = Store.objects.create(name='McDonalds')
        MenuItem.objects.create(store=mcdonalds, name='大麥克餐', price=99)

    def tearDown(self):
        Store.objects.all().delete()

    def test_home_view(self):
        r = self.client.get('/store/')
        self.assertContains(
            r, '<a class="navbar-brand" href="/">午餐系統</a>',
            html=True,
        )
        self.assertContains(r, '<a href="/store/1/">肯德基</a>', html=True)
        self.assertContains(r, '薄皮嫩雞')

    def test_detail_view(self):
        r = self.client.get('/store/2/')
        self.assertContains(
            r, '<tr><td>大麥克餐</td><td>99</td></tr>',
            html=True,
        )
