from django.test import TestCase

from ..models import Group, Post, Comment, Follow, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Стихи',
            slug='poetry',
            description='Различные стихотворения'
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Пам - Пам - Пам - Пам - Пам - Пам -',

        )

        cls.comment = Comment(
            post=cls.post,
            author=cls.user,
            text='Тестовый коммент',
        )

    def test_str(self):
        group = PostModelTest.group
        post = PostModelTest.post
        comment = PostModelTest.comment
        self.assertEqual(str(post), 'Пам - Пам - Пам')
        self.assertEqual(str(group), 'Стихи')
        self.assertEqual(str(comment), 'Тестовый коммен')

    def test_verbose(self):
        group = PostModelTest.group
        post = PostModelTest.post

        self.assertEqual(post._meta.get_field('text').verbose_name,
                         'Текст поста')
        self.assertEqual(group._meta.get_field('title').verbose_name,
                         'Заголовок')

    def test_follow(self):
        user = PostModelTest.user
        another_user = User.objects.create_user(username='another_user')
        follow = Follow(
            user=user,
            author=another_user,
        )
        self.assertEqual(follow._meta.get_field('user').verbose_name,
                         'Подписчик')
        self.assertEqual(follow._meta.get_field('author').verbose_name,
                         'Автор')

    def test_comment(self):
        comment = PostModelTest.comment
        self.assertEqual(comment._meta.get_field('text').verbose_name,
                         'Текст Комментария')
        self.assertEqual(comment._meta.get_field('post').verbose_name,
                         'Пост')
        self.assertEqual(comment._meta.get_field('author').verbose_name,
                         'Автор')
