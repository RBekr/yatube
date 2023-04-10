import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache

from ..models import Post, Group, Comment, Follow, User


USER_NAME = 'auth'
GROUP_SLUG = 'test-slug'
MAIN_PAGE = reverse('posts:index')
CREATE_POST_PAGE = reverse('posts:post_create')
PROFILE_PAGE = reverse('posts:profile',
                       kwargs={'username': USER_NAME})
GROUP_PAGE = reverse('posts:group_list', kwargs={'slug': GROUP_SLUG})
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
PROFILE_UNFOLLOW = reverse('posts:profile_unfollow',
                           kwargs={'username': USER_NAME})
PROFILE_FOLLOW = reverse('posts:profile_follow',
                         kwargs={'username': USER_NAME})
FOLLOW_INDEX = reverse('posts:follow_index')
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username=USER_NAME)
        cls.authorized_client = Client()

        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=uploaded,
        )
        Comment.objects.create(
            author=cls.user,
            text='Тестовый коммент',
            post=cls.post,
        )
        cls.POST_DETAIL_PAGE = reverse('posts:post_detail',
                                       kwargs={'post_id': cls.post.id})
        cls.POST_EDIT_PAGE = reverse('posts:post_edit',
                                     kwargs={'post_id': cls.post.id})

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def tearDown(cls):
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_pages_names = {
            MAIN_PAGE: 'posts/index.html',
            GROUP_PAGE: 'posts/group_list.html',
            PROFILE_PAGE: 'posts/profile.html',
            self.POST_DETAIL_PAGE: 'posts/post_detail.html',
            self.POST_EDIT_PAGE: 'posts/create_post.html',
            CREATE_POST_PAGE: 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template, reverse_name)

    def test_post_form(self):
        reverses = (self.POST_EDIT_PAGE, CREATE_POST_PAGE,)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for reverse_name in reverses:
            response = self.authorized_client.get(reverse_name)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_post_in_pages(self):
        reverses = (
            MAIN_PAGE,
            GROUP_PAGE,
            PROFILE_PAGE,
        )

        for reverse_name in reverses:
            with self.subTest(value=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIn(self.post, response.context['page_obj'])
                self.assertEqual(
                    self.post.image,
                    response.context['page_obj'][0].image
                )

    def test_post_not_in_group(self):
        new_post = Post.objects.create(
            author=self.user,
            text='Тестовый текст',
        )
        response = self.authorized_client.get(GROUP_PAGE)
        self.assertNotIn(new_post, response.context['page_obj'])

    def test_post_detail_correct_context_(self):
        response = self.client.get(self.POST_DETAIL_PAGE)
        self.assertIsInstance(response.context.get('post'), Post)
        self.assertEqual(response.context.get('post').id, self.post.id)
        self.assertEqual(response.context.get('post').image, self.post.image)

        self.assertEqual(response.context['post'].comments.all()[0].text,
                         Comment.objects.filter(post=self.post)[0].text)

    def test_post_list_cache_index(self):
        response_old = self.client.get(MAIN_PAGE)
        Post.objects.create(
            author=self.user,
            text='Тестовый текст',
        )
        response = self.client.get(MAIN_PAGE)
        self.assertEqual(response_old.content, response.content)
        cache.clear()
        response_new = self.client.get(MAIN_PAGE)
        self.assertNotEqual(response.content, response_new.content)

    def test_user_follow(self):
        new_user = User.objects.create(
            username='new'
        )
        new_authorized_client = Client()
        new_authorized_client.force_login(new_user)
        new_authorized_client.get(PROFILE_FOLLOW)
        follow_index_response1 = new_authorized_client.get(FOLLOW_INDEX)
        self.assertIn(self.post, follow_index_response1.context['page_obj'])
        self.assertTrue(
            Follow.objects.filter(
                user=new_user,
                author=self.user,
            ).exists()
        )
        new_authorized_client.get(PROFILE_UNFOLLOW)
        follow_index_response2 = new_authorized_client.get(FOLLOW_INDEX)
        self.assertFalse(
            Follow.objects.filter(
                user=new_user,
                author=self.user,
            ).exists()
        )
        self.assertNotIn(self.post,
                         follow_index_response2.context['page_obj'])


class PaginatorViewsTest(TestCase):
    FIRST_PAGE_COUNT = 10
    TOTAL_COUNT = 13
    TEST_COUNT = [(1, FIRST_PAGE_COUNT),
                  (2, TOTAL_COUNT - FIRST_PAGE_COUNT)]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='auth')
        cls.authorized_client = Client()

        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        Post.objects.bulk_create(
            [Post(author=cls.user, text='Тестовый текст',
             group=cls.group) for i in range(cls.TOTAL_COUNT)]
        )

    @classmethod
    def tearDown(cls):
        cache.clear()

    def test_page_contains_records_index(self):

        for test_count in self.TEST_COUNT:
            page, count = test_count
            with self.subTest(value=page):
                response = self.client.get(MAIN_PAGE, {'page': page})
                self.assertEqual(len(response.context['page_obj']), count)

    def test_page_contains_records_group_list(self):

        for test_count in self.TEST_COUNT:
            page, count = test_count
            with self.subTest(value=page):
                response = self.client.get(GROUP_PAGE, {'page': page})
                self.assertEqual(len(response.context['page_obj']), count)
                for obj in response.context['page_obj']:
                    with self.subTest(value=str(obj)):
                        self.assertEqual(obj.group, self.group)

    def test_page_contains_records_profile(self):
        for test_count in self.TEST_COUNT:
            page, count = test_count
            with self.subTest(value=page):
                response = self.client.get(PROFILE_PAGE, {'page': page})
                self.assertEqual(len(response.context['page_obj']), count)
                for obj in response.context['page_obj']:
                    with self.subTest(value=str(obj)):
                        self.assertEqual(obj.author, self.user)
