from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Group, Post, Follow
from .forms import PostForm, CommentForm

User = get_user_model()

N_POSTS_IN_PAGE = 10
CACHE_TIME = 20


@cache_page(CACHE_TIME, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'
    posts_list = Post.objects.all()
    paginator = Paginator(posts_list, N_POSTS_IN_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.posts.all()
    paginator = Paginator(posts_list, N_POSTS_IN_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    template = 'posts/group_list.html'
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, template, context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    following = (request.user.is_authenticated
                 and user.following.filter(user=request.user).exists())
    posts_list = user.posts.all()
    paginator = Paginator(posts_list, N_POSTS_IN_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'author': user,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = User.objects.get(username=post.author)
    form = CommentForm()
    context = {
        'form': form,
        'post': post,
        'author': user,
    }
    return render(request, 'posts/post_detail.html', context)


@csrf_exempt
def post_create(request):
    is_edit = False
    form = PostForm(request.POST or None,
                    files=request.FILES or None,)
    context = {
        'form': form,
        'is_edit': is_edit,
    }
    if request.user.is_authenticated:
        username = request.user.username
        if request.method == 'POST':
            if form.is_valid():
                post = form.save(commit=False)
                post.author = request.user
                post.save()
                return redirect('posts:profile', username)
            return render(request, 'posts/create_post.html',
                          context=context)
        return render(request, 'posts/create_post.html', context=context)
    return redirect('users:login')


@csrf_exempt
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    is_edit = True
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            return redirect('posts:post_detail', post_id)

    context = {
        'form': form,
        'is_edit': is_edit,
    }
    return render(request, 'posts/create_post.html', context=context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    following_posts = Post.objects.filter(author__following__user=user)
    paginator = Paginator(following_posts, N_POSTS_IN_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)

    existing_follow = Follow.objects.filter(
        user=request.user,
        author=author,
    )
    if request.user != author and not existing_follow.exists():
        Follow.objects.create(
            user=request.user,
            author=author,
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = User.objects.get(username=username)
    if request.user != author:
        Follow.objects.get(
            user=request.user,
            author=author,
        ).delete()
    return redirect('posts:profile', username)
