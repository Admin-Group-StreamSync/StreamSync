"""
Step definitions for authentication.feature
"""
from unittest.mock import patch

from behave import given, when, then
from django.contrib.auth.models import User
from django.urls import reverse

_HOME_MOVIES = "apps.users.views.get_all_movies"
_HOME_SERIES = "apps.users.views.get_all_series"
_HOME_GENRES = "apps.users.views.get_genres_from_api"
_HOME_RATINGS = "apps.users.views.get_age_ratings_from_api"
_HOME_ENRICH = "apps.users.views.enrich_tmdb_images"
_REG_GENRES = "apps.users.views.get_genres_from_api"
_REG_RATINGS = "apps.users.views.get_age_ratings_from_api"


# ---------------------------------------------------------------------------
# Given
# ---------------------------------------------------------------------------

@given("the application is running")
def step_app_running(context):
    pass  # Django is set up in environment.py


@given("I am an anonymous user")
def step_anonymous(context):
    context.client.logout()


@given('a user "{username}" with password "{password}" exists')
def step_user_exists(context, username, password):
    context.user = User.objects.create_user(username=username, password=password)


@given('I am logged in as "{username}" with password "{password}"')
def step_logged_in(context, username, password):
    context.client.login(username=username, password=password)


@given("I am logged out")
def step_logged_out(context):
    context.client.logout()


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------

@when('I register with username "{username}" and password "{password}"')
def step_register(context, username, password):
    with patch(_REG_GENRES, return_value=[]), patch(_REG_RATINGS, return_value=[]):
        context.response = context.client.post(reverse("registre"), {
            "username": username,
            "first_name": "Test User",
            "email": f"{username}@test.com",
            "password1": password,
            "password2": password,
        })



@when("I visit the home page")
def step_visit_home(context):
    context.response = context.client.get(reverse("pagina_principal"))


@when("I visit the home page with mocked API")
def step_visit_home_mocked(context):
    with patch(_HOME_MOVIES, return_value=[]), \
         patch(_HOME_SERIES, return_value=[]), \
         patch(_HOME_GENRES, return_value=[]), \
         patch(_HOME_RATINGS, return_value=[]), \
         patch(_HOME_ENRICH, side_effect=lambda x: x):
        context.response = context.client.get(reverse("pagina_principal"))


@when('I login as "{username}" with password "{password}"')
def step_login(context, username, password):
    context.response = context.client.post(reverse("login"), {
        "username": username,
        "password": password,
    })


@when("I visit the password change page")
def step_visit_pwd_change(context):
    context.response = context.client.get(reverse("cambiar_password"))


@when('I change my password from "{old}" to "{new}"')
def step_change_password(context, old, new):
    context.response = context.client.post(reverse("cambiar_password"), {
        "old_password": old,
        "new_password1": new,
        "new_password2": new,
    })


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------

@then('a user account is created for "{username}"')
def step_user_created(context, username):
    assert User.objects.filter(username=username).exists(), \
        f"User '{username}' was not created"


@then('the profile for "{username}" exists')
def step_profile_exists(context, username):
    from apps.users.models.models import Profile
    user = User.objects.get(username=username)
    assert Profile.objects.filter(user=user).exists(), "Profile does not exist"


@then('the profile for "{username}" has platform "{platform}"')
def step_profile_has_platform(context, username, platform):
    user = User.objects.get(username=username)
    assert platform in user.profile.plataformes, \
        f"Platform '{platform}' not in profile platforms: {user.profile.plataformes}"


@then("I am redirected to the login page")
def step_redirected_to_login(context):
    assert context.response.status_code == 302, \
        f"Expected 302, got {context.response.status_code}"
    assert "login" in context.response["Location"].lower(), \
        f"Expected redirect to login, got {context.response['Location']}"


@then("the login is successful")
def step_login_successful(context):
    assert context.response.status_code in [200, 302], \
        f"Expected 200 or 302, got {context.response.status_code}"


@then("the login page is shown again")
def step_login_page_shown(context):
    assert context.response.status_code == 200, \
        f"Expected 200, got {context.response.status_code}"


@then("the response status is {status:d}")
def step_response_status(context, status):
    assert context.response.status_code == status, \
        f"Expected {status}, got {context.response.status_code}"


@then("I am redirected after password change")
def step_redirected_after_pwd(context):
    assert context.response.status_code == 302, \
        f"Expected redirect (302), got {context.response.status_code}"