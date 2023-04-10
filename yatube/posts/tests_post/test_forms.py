import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from ..models import Post, Group, Comment, User


USER_NAME = 'auth'
CREATE_POST_PAGE = reverse('posts:post_create')
PROFILE_PAGE = reverse('posts:profile',
                       kwargs={'username': USER_NAME})
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USER_NAME)
        cls.authorized_client = Client()
        cls.guest_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )
        cls.POST_DETAIL_PAGE = reverse('posts:post_detail',
                                       kwargs={'post_id': cls.post.id})
        cls.POST_EDIT_PAGE = reverse('posts:post_edit',
                                     kwargs={'post_id': cls.post.id})
        cls.ADD_COMMENT = reverse('posts:add_comment',
                                  kwargs={'post_id': cls.post.id})

    @classmethod
    def tearDown(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        count_posts = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый пост',
            'group': self.group.id,
            'image': uploaded,

        }
        response = self.authorized_client.post(
            CREATE_POST_PAGE,
            data=form_data,
        )
        self.assertRedirects(response, PROFILE_PAGE)
        self.assertEqual(Post.objects.count(), count_posts + 1)
        latest_post = Post.objects.latest('id')
        self.assertTrue(latest_post.text == 'Новый пост')
        self.assertTrue(latest_post.group == self.group)
        self.assertTrue(latest_post.image == 'posts/small.gif')

    def test_edit_post(self):
        count_posts = Post.objects.count()

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый пост',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            self.POST_EDIT_PAGE,
            data=form_data,
        )
        self.assertRedirects(response, self.POST_DETAIL_PAGE)
        self.assertEqual(Post.objects.count(), count_posts)
        self.assertTrue(
            Post.objects.filter(
                text='Новый пост',
                group=self.group,
                image='posts/small.gif',
            ).exists()
        )

    def test_authorized_create_comment(self):
        count_com = Comment.objects.count() + 1
        count_com_by_post = self.post.comments.count() + 1
        form_data = {
            'text': 'Тестовый коммент',
        }
        response = self.authorized_client.post(
            self.ADD_COMMENT,
            data=form_data,
        )
        self.assertRedirects(response, self.POST_DETAIL_PAGE)
        self.assertEqual(Comment.objects.count(), count_com)
        self.assertEqual(self.post.comments.count(), count_com_by_post)
        self.assertTrue(
            Comment.objects.filter(
                text='Тестовый коммент',
                post=self.post,
            ).exists()
        )

    def test_anonymous_create_comment(self):
        count_com = Comment.objects.count()
        count_com_by_post = self.post.comments.count()
        form_data = {
            'text': 'Тестовый коммент',
        }
        self.guest_client.post(
            self.ADD_COMMENT,
            data=form_data,
        )
        self.assertEqual(Comment.objects.count(), count_com)
        self.assertEqual(self.post.comments.count(), count_com_by_post)
