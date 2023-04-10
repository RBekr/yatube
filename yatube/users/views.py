from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import smart_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.views.generic import CreateView
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.forms import (PasswordChangeForm,
                                       PasswordResetForm)

from .forms import CreationForm

User = get_user_model()


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


class PasswordsChangeView(PasswordChangeView):

    form_class = PasswordChangeForm
    success_url = reverse_lazy('users:password_change_done')


def send_msg(request, user, theme, text, email, fail_silently):
    subject = theme
    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
    relativelink = f'/auth/reset/{uidb64}/{token}'

    current_site = get_current_site(request=request).domain
    absurl = 'http://' + current_site + relativelink
    email_body = ('Hello, \n Use link below to reset your password  \n'
                  + absurl)
    body = f'''{text}
               email: {email}
               token: {token}
               link: {email_body}
            '''

    from_email = 'yatube@example.com'

    send_mail(
        subject, body, from_email, [email], fail_silently=fail_silently,
    )


@csrf_exempt
def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.get(email=email)

            if user:
                send_msg(request, user, 'Тема письма', 'Текст письма.',
                         email, fail_silently=False)
                return redirect('users:password_reset_done')
        else:
            return redirect('users:password_reset_form')

    form = PasswordResetForm()
    return render(request, 'users/password_reset_form.html', {'form': form})
