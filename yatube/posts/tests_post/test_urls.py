from django.test import TestCase, Client
from http import HTTPStatus

from ..models import Post, Group, User


GROUP_SLUG = 'test-slug'
USERNAME = 'auth'
MAIN_PAGE = '/'
GROUP_PAGE = f'/group/{GROUP_SLUG}/'
PROFILE_PAGE = f'/profile/{USERNAME}/'
CREARE_PAGE = '/create/'
LOGIN_PAGE = '/auth/login/'


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.authorized_client = Client()

        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )
        cls.POST_DETAIL_PAGE = f'/posts/{cls.post.id}/'
        cls.POST_EDIT_PAGE = f'/posts/{cls.post.id}/edit/'

    def test_unexisting(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html',)

    def test_urlsguest_client_template(self):
        templates_url_names = {
            MAIN_PAGE: 'posts/index.html',
            GROUP_PAGE: 'posts/group_list.html',
            PROFILE_PAGE: 'posts/profile.html',
            self.POST_DETAIL_PAGE: 'posts/post_detail.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urlsguest_client_redirect(self):
        templates_url_names = {
            self.POST_EDIT_PAGE: self.POST_DETAIL_PAGE,
            CREARE_PAGE: LOGIN_PAGE,
        }
        for address, redirect in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertRedirects(response, redirect)

    def test_urls_author(self):
        templates_url_names = {
            self.POST_EDIT_PAGE: 'posts/create_post.html',
            CREARE_PAGE: 'posts/create_post.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_post_edit_notauthor(self):
        not_author = User.objects.create_user(username='not_auth')
        not_author_authorized_client = Client()
        not_author_authorized_client.force_login(not_author)
        response = not_author_authorized_client.get(self.POST_EDIT_PAGE)
        self.assertRedirects(response, self.POST_DETAIL_PAGE)
