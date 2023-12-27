from base64 import urlsafe_b64decode
import struct
from base64 import urlsafe_b64encode
from django.core.mail import EmailMessage
from django.contrib import messages, auth
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from accounts.models import Account
from .forms import RegistrationForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode


# Create your views here.


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split('@')[0]

            user = Account.objects.create_user(
                first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number
            user.save()

            # user activation
            current_site = get_current_site(request)
            mail_subject = "please activate your account"
            message = render_to_string("PixelCart/account_verification_email.html", {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_b64encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user)
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[email])
            send_email.send()

            # messages.success(
            #     request, "Thank you for registering. We have sent an verificaion mail.")
            return redirect("/accounts/login/?command=verification&email=" + email)
    else:
        form = RegistrationForm()
    context = {
        "form": form,
    }
    return render(request, "PixelCart/register.html", context)


def login(request):
    if request.method == "POST":
        email = request.POST.get('email', '')

        # Check if 'password' key is in request.POST
        if 'password' not in request.POST:
            messages.error(request, "Password is required")
            return redirect("login")

        password = request.POST['password']

        user = auth.authenticate(email=email.lower(), password=password)

        if user is not None:
            auth.login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid Email or Password")
            return redirect("login")
    return render(request, "PixelCart/login.html")


@login_required(login_url="login")
def logout(request):
    auth.logout(request)
    messages.success(request, "Log Out Succesfully")
    return redirect("login")


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(
            request, 'Congratulations! Your account is activated.')
        return redirect('login')
    else:
        messages.error(request, 'Invalid activation link')
        return redirect('register')


@login_required(login_url="login")
def dashboard(request):
    return render(request, "PixelCart/dashboard.html")


def forgotPassword(request):
    if request.method == "POST":
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            # Reset Password

            current_site = get_current_site(request)
            mail_subject = " Reset your password"
            message = render_to_string("PixelCart/reset_password_email.html", {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_b64encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user)
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[email])
            send_email.send()
            messages.success(
                request, "Password email address has been sent to your email address")
            return redirect("login")

        else:
            messages.error(request, "Account does not exists")
            return redirect("forgotPassword")
    return render(request, "PixelCart/forgotPassword.html")


def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session[uid] = uid
        messages.success(request, "Please reset your password")
        return redirect("resetPassword")
    else:
        messages.error(request, "This link has beeen expired")
        return redirect("login")


def resetPassword(request):
    if request.method == "POST":
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            messages.success(request, "Password reset successfully")
            return redirect("login")

        else:
            messages.error(request, "Password do not match ")
    else:
        return render(request, "PixelCart/resetPassword.html")
