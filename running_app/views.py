from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AdminPasswordChangeForm, PasswordChangeForm, UserChangeForm
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from datetime import datetime

from social_django.models import UserSocialAuth
from running_app.models import GpxFile, UserProfile
from running_app.forms import UserForm, UserProfileForm, GpxForm


def home(request):
    user = request.user
    if user.is_authenticated():
        auth_providers = []
        try:
            user_profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            user_profile = None
        if user_profile is not None:
            gpx_files = GpxFile.objects.filter(user_profile=user_profile)
        else:
            gpx_files = None
        context_dict = {
            'gpx_files': gpx_files,
        }

    else:
        context_dict = {}

    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']
    context_dict['last_visit'] = request.session['last_visit']

    return render(request, 'running/home.html', context_dict)


def suggestions(request):
    user = request.user
    if user.is_authenticated():
        auth_providers = []
        try:
            user_profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            user_profile = None
        if user_profile is not None:
            gpx_files = GpxFile.objects.exclude(user_profile=user_profile)
        else:
            gpx_files = None
        context_dict = {
            'gpx_files': gpx_files,
        }

    else:
        return render(request, 'running/home.html', {})

    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']
    context_dict['last_visit'] = request.session['last_visit']

    return render(request, 'running/suggestions.html', context_dict)


def upload(request):
    if not request.user.is_authenticated:
        return render(request, 'running/home.html', {})
    else:
        uploaded = False

        if request.method == 'POST':
            user = request.user
            user_profile = UserProfile.objects.get_or_create(user=user)[0]
            gpx_form = GpxForm(data=request.POST)

            if gpx_form.is_valid() and 'gpx_file' in request.FILES:
                user_profile.save()

                gpx = gpx_form.save(commit=False)
                gpx.user_profile = user_profile
                gpx.gpx_file = request.FILES['gpx_file']

                gpx.save()

                uploaded = True
            else:
                print(gpx_form.errors)
        else:
            gpx_form = GpxForm()
        context_dict = {'gpx_form': gpx_form, 'uploaded': uploaded}
        return render(request, 'running/upload.html', context_dict)


def about(request):
    context_dict = {'author': "Chris Watson - 2190594W"}
    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']
    context_dict['last_visit'] = request.session['last_visit']
    context_dict['nbar'] = 'about'
    return render(request, 'running/about.html', context_dict)


def register(request):
    if request.user.is_authenticated:
        return render(request, 'running/register.html',
                  {'logged_in': True})
    else:
        registered = False

        if request.method == 'POST':
            user_form = UserForm(data=request.POST)
            profile_form = UserProfileForm(data=request.POST)

            if user_form.is_valid() and profile_form.is_valid():
                user = user_form.save()
                user.set_password(user.password)
                user.save()

                profile = profile_form.save(commit=False)
                profile.user = user

                if 'picture' in request.FILES:
                    profile.picture = request.FILES['picture']

                profile.save()

                registered = True
            else:
                print(user_form.errors, profile_form.errors)
        else:
            user_form = UserForm()
            profile_form = UserProfileForm()
        context_dict = {'user_form': user_form, 'profile_form': profile_form, 'registered': registered}
        return render(request, 'running/register.html', context_dict)



def user_login(request):
    if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(username=username, password=password)

            if user:
                if user.is_active:
                    login(request, user)
                    return HttpResponseRedirect(reverse('home'))
                else:
                    return HttpResponse("Your Policy Tracker account is disabled.")
            else:
                errorMessage = "Invalid login details. Username '{0}' does not match the password provided.".format(username)
                return render(request, 'running/login.html', {'error': errorMessage, 'username': format(username)})
    else:
        return render(request, 'running/login.html', {})

@login_required
def profile_settings(request):
    user = request.user

    try:
        google_login = user.social_auth.get(provider='google-oauth2')
    except UserSocialAuth.DoesNotExist:
        google_login = None

    try:
        github_login = user.social_auth.get(provider='github')
    except UserSocialAuth.DoesNotExist:
        github_login = None

    try:
        twitter_login = user.social_auth.get(provider='twitter')
    except UserSocialAuth.DoesNotExist:
        twitter_login = None

    try:
        facebook_login = user.social_auth.get(provider='facebook')
    except UserSocialAuth.DoesNotExist:
        facebook_login = None

    can_disconnect = (user.social_auth.count() > 1 or user.has_usable_password())

    return render(request, 'running/profile_settings.html', {
        'google_login': google_login,
        'github_login': github_login,
        'twitter_login': twitter_login,
        'facebook_login': facebook_login,
        'can_disconnect': can_disconnect
    })

@login_required
def profile_password(request):
    if request.user.has_usable_password():
        PasswordForm = PasswordChangeForm
    else:
        PasswordForm = AdminPasswordChangeForm

    if request.method == 'POST':
        form = PasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordForm(request.user)
    return render(request, 'running/profile_password.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('home'))

def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val

def visitor_cookie_handler(request):
    visits = int(get_server_side_cookie(request, 'visits', '1'))
    last_visit_cookie = get_server_side_cookie(request, 'last_visit', str(datetime.now()))
    last_visit_time = datetime.strptime(last_visit_cookie[:-7], '%Y-%m-%d %H:%M:%S')

    if (datetime.now() - last_visit_time).days > 0:
        visits = visits + 1

        request.session['last_visit'] = str(datetime.now())
    else:
        visits = 1

        request.session['last_visit'] = last_visit_cookie

    request.session['visits'] = visits

def contactus(request):
    context_dict = {}
    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']
    context_dict['last_visit'] = request.session['last_visit']
    return render(request, 'running/contactus.html', context_dict)

def faq(request):
    context_dict = {}
    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']
    context_dict['last_visit'] = request.session['last_visit']
    return render(request, 'running/faq.html', context_dict)

def news(request):
    context_dict = {}
    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']
    context_dict['last_visit'] = request.session['last_visit']
    context_dict['nbar'] = 'news'
    return render(request, 'running/news.html', context_dict)


# def country(request, country_name_slug):
#     context_dict = {}
#     policy_statuses = {'No Progress': 0, 'In Progress': 0, "Achieved": 0, 'Broken': 0}
#     status_fillers = []
#
#     try:
#         country = Country.objects.get(slug=country_name_slug)
#         policies = Policy.objects.filter(country=country)
#         context_dict['country'] = country
#         context_dict['policies'] = policies
#         for policy in policies:
#             policy_statuses[policy.status.name] += 1
#         noProgress = policy_statuses['No Progress']
#         inProgress = policy_statuses['In Progress']
#         achieved = policy_statuses['Achieved']
#         broken = policy_statuses['Broken']
#         policy_statuses = [noProgress, inProgress, achieved, broken]
#         if len(policies) > 0:
#             status_fillers = [
#                 ((float(noProgress)/float(len(policies)))*100),
#                 ((float(inProgress)/float(len(policies)))*100),
#                 ((float(achieved)/float(len(policies)))*100),
#                 ((float(broken)/float(len(policies)))*100),
#             ]
#
#     except Country.DoesNotExist:
#         context_dict['country'] = None
#         context_dict['policies'] = None
#
#     context_dict['policy_statuses'] = policy_statuses
#     context_dict['status_fillers'] = status_fillers
#     context_dict['policy_table'] = True
#     return render(request, 'running/country.html', context_dict)
#
#
# def countries(request):
#     country_list = Country.objects.all()
#     policy_list = []
#     for country in country_list:
#         policy_list.append(Policy.objects.filter(country=country))
#     context_dict = {'countries': country_list, 'policies': policy_list}
#     visitor_cookie_handler(request)
#     context_dict['visits'] = request.session['visits']
#     context_dict['last_visit'] = request.session['last_visit']
#     context_dict['nbar'] = 'countries'
#     return render(request, 'running/countries.html', context_dict)
#
#
# @login_required
# def add_country(request):
#     if request.method == 'POST':
#         country_form = CountryForm(data=request.POST)
#
#         if country_form.is_valid():
#             country = country_form.save(commit=False)
#
#             if 'background_image' in request.FILES:
#                 country.background_image = request.FILES['background_image']
#             if 'map_image' in request.FILES:
#                 country.map_image = request.FILES['map_image']
#
#             country.save()
#
#             return HttpResponseRedirect('/countries/' + country.slug)
#         else:
#             print(country_form.errors)
#     else:
#         country_form = CountryForm()
#
#     return render(request, 'running/add_country.html', {"country_form": country_form, 'add_country': True})
#
# @login_required
# def add_policy(request, country_name_slug):
#     context_dict = {}
#     try:
#         country = Country.objects.get(slug=country_name_slug)
#     except Country.DoesNotExist:
#         context_dict['country'] = None
#         return render(request, 'running/add_policy.html', context_dict)
#
#     if request.method == 'POST':
#         policy_form = PolicyForm(data=request.POST)
#
#         if policy_form.is_valid():
#             policy = policy_form.save(commit=False)
#
#             policy.country = country
#
#             policy.save()
#
#             return HttpResponseRedirect('/policy/' + str(policy.id))
#         else:
#             print(policy_form.errors)
#     else:
#         policy_form = PolicyForm()
#
#
#     return render(request, 'running/add_policy.html', {"policy_form": policy_form, 'country': country})
#
#
# @login_required
# def policy(request, policy_id):
#     try:
#         policy = Policy.objects.get(id=policy_id)
#     except Policy.DoesNotExist:
#         policy = None
#         return render(request, 'running/policy.html', {'policy': policy, 'policy_id': policy_id})
#
#     return render(request, 'running/policy.html', {'policy': policy})
