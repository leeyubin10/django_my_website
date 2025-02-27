from unicodedata import category

from django.test import TestCase, Client
from bs4 import BeautifulSoup
from .models import Post, Category, Tag
from django.utils import timezone
from django.contrib.auth.models import User


def create_category(name='life', description=''):
    category, is_created = Category.objects.get_or_create(
        name=name,
        description=description
    )
    category.slug = category.name.replace(' ', '-').replace('/', '')
    category.save()

    return category


def create_tag(name='some_tag'):
    tag, is_created = Tag.objects.get_or_create(
        name=name
    )
    tag.slug = tag.name.replace(' ', '-').replace('/', '')
    tag.save()

    return tag


def create_post(title, content, author, category=None):
    blog_post = Post.objects.create(
        title=title,
        content=content,
        created=timezone.now(),
        author=author,
        category=category,
    )

    return blog_post


class TestModel(TestCase):
    def setUp(self):
        self.client = Client()
        self.author_000 = User.objects.create(username='smith', password='nopassword')

    def test_category(self):
        category = create_category()

        post_000 = create_post(
            title='The first post',
            content='Hello World. We are the world.',
            author=self.author_000,
            category=category,
        )

        self.assertEqual(category.post_set.count(), 1)

    def test_tag(self):
        tag_000 = create_tag(name='bad_guy')
        tag_001 = create_tag(name='america')

        post_000 = create_post(
            title='The first post',
            content='Hello World. We are the world.',
            author=self.author_000,
        )
        post_000.tags.add(tag_000)
        post_000.tags.add(tag_001)
        post_000.save()

        post_001 = create_post(
            title='Stay Fool, Stay Hungry',
            content='Story about Steve Jobs',
            author=self.author_000
        )
        post_001.tags.add(tag_001)
        post_001.save()

        self.assertEqual(post_000.tags.count(), 2)  # post는 여러개의 tag를 가질 수 있다.
        self.assertEqual(tag_001.post_set.count(), 2)  # 하나의 tag는 여러개의 post에 붙을 수 있다.
        self.assertEqual(tag_001.post_set.first(), post_000)  # 하나의 tag는 자신을 가진 post들을 불러올 수 있다.
        self.assertEqual(tag_001.post_set.last(), post_001)  # 하나의 tag는 자신을 가진 post들을 불러올 수 있다.

    def test_post(self):
        category = create_category()

        post_000 = create_post(
            title='The first post',
            content='Hello World. We are the world.',
            author=self.author_000,
            category=category,
        )


class TestView(TestCase):
    def setUp(self):
        self.client = Client()
        self.author_000 = User.objects.create(username='smith', password='nopassword')

    def check_navbar(self, soup):
        navbar = soup.find('div', id='navbar')
        self.assertIn('Blog', navbar.text)
        self.assertIn('About me', navbar.text)

    def check_right_side(self, soup):
        category_card = soup.find('div', id='category-card')
        self.assertIn('미분류 (1)', category_card.text)  # 미분류 (1) 있어야 함
        self.assertIn('정치/사회 (1)', category_card.text)  # 정치/사회 (1) 있어야 함

    def test_post_list(self):
        response = self.client.get('/blog/')
        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.title

        self.assertIn(title.text, 'Blog')

        self.check_navbar(soup)

        self.assertEqual(Post.objects.count(), 0)
        self.assertIn('아직 게시물이 없습니다.', soup.body.text)

    def test_post_list_no_post(self):

        post_000 = create_post(
            title='The first post',
            content='Hello World. We are the world.',
            author=self.author_000,
        )

        post_001 = create_post(
            title='The second post',
            content='Second Second Second',
            author=self.author_000,
            category=create_category(name='정치/사회')
        )

        self.assertGreater(Post.objects.count(), 0)

        response = self.client.get('/blog/')
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        body = soup.body
        self.assertNotIn('아직 게시물이 없습니다.', body.text)
        self.assertIn(post_000.title, body.text)

        post_000_read_more_btn = body.find('a', id='read-more-post-{}'.format(post_000.pk))
        self.assertEqual(post_000_read_more_btn['href'], post_000.get_absolute_url())

        # category card 에서
        self.check_right_side(soup)

        # main div에는
        main_div = soup.find('div', id='main-div')
        self.assertIn('정치/사회', main_div.text)  # 첫번째 포스트에는 '정치/사회 있어야 함
        self.assertIn('미분류', main_div.text)  # main div에는 '미분류' 있어야 함

    def test_post_detail(self):
        post_000 = create_post(
            title='The first post',
            content='Hello World. We are the world.',
            author=self.author_000,
        )

        post_001 = create_post(
            title='The second post',
            content='Second Second Second',
            author=self.author_000,
            category=create_category(name='정치/사회')
        )

        self.assertGreater(Post.objects.count(), 0)
        post_000_url = post_000.get_absolute_url()
        self.assertEqual(post_000_url, '/blog/{}/'.format(post_000.pk))

        response = self.client.get(post_000_url)
        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.title

        self.assertEqual(title.text, '{} - Blog'.format(post_000.title))

        self.check_navbar(soup)

        body = soup.body

        main_div = body.find('div', id='main-div')
        self.assertIn(post_000.title, main_div.text)
        self.assertIn(post_000.author.username, main_div.text)

        self.assertIn(post_000.content, main_div.text)

        self.check_right_side(soup)

    def test_post_list_no_category(self):
        category_politics = create_category(name='정치/사회')
        post_00 = create_post(
            title='The first post',
            content='Hello World. We are the world.',
            author=self.author_000,
        )

        post_001 = create_post(
            title='The second post',
            content='Second Second Second',
            author=self.author_000,
            category=category_politics
        )

        response = self.client.get('/blog/category/_none/')
        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.content, 'html.parser')
        # self.assertEqual('Blog - {}'.format(category_politics.name), soup.title.text)

        main_div = soup.find('div', id='main-div')
        self.assertIn('미분류', main_div.text)
        self.assertNotIn(category_politics.name, main_div.text)