from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.forms.forms import Form
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect

from my_site.forms import UserForm, propertyFormSet, meetingFormSet, clientForm, UserProfileForm, UForm
from my_site.models import Client, User
from my_site.utils import getDictionary


def index(request):
    # users = getDictionary(User.objects.all(), exclude=["password"], rename={"id": "email", "email": "username"})
    # clients = getDictionary(Client.objects.all())
    # return JsonResponse({"users": users, "clients": clients})
    return render(request, 'my_site/views/index.html', {'users': User.objects.all(), 'clients': Client.objects.all(), })


def user(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(user.password)
            user.save()
            return redirect('my_site:userInfo', id=user.id)
    else:
        form = UserForm
    return render(request, 'my_site/views/create.html', {'form': [form, ], "title": "user"})


def client(request):
    if request.method == "POST":
        form = clientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=True)
            return redirect('my_site:clientInfo', id=client.id)
    else:
        form = clientForm
    return render(request, 'my_site/views/create.html', {'form': [form, ], "title": "client"})


def userInfo(request, id):
    user = get_object_or_404(User, pk=id)
    if request.method == "POST":
        form = propertyFormSet(request.POST, instance=user)
        if form.is_valid():
            properties = form.save(commit=True)
            return redirect('my_site:userInfo', id=id)
    else:
        form = propertyFormSet(instance=user)
    return render(request, 'my_site/views/user.html', {'owner': user, 'form': form})


def clientInfo(request, id):
    client = get_object_or_404(Client, pk=id)
    if request.method == "POST":
        form = meetingFormSet(request.POST, instance=client)
        if form.is_valid():
            meetings = form.save(commit=True)
            return redirect('my_site:clientInfo', id=id)
    else:
        form = meetingFormSet(instance=client)
    return render(request, 'my_site/views/client.html', {'client': client, 'form': form})


def userDelete(request, id):
    user = get_object_or_404(User, pk=id)
    if request.method == "POST":
        form = Form(request.POST)
        if form.is_valid():
            user.delete()
    return redirect('my_site:index')


def clientDelete(request, id):
    client = get_object_or_404(Client, pk=id)
    if request.method == "POST":
        form = Form(request.POST)
        if form.is_valid():
            client.delete()
    return redirect('my_site:index')


def register(request):
    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save(commit=False)

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()

            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user

            # Did the user provide a profile picture?
            # If so, we need to get it from the input form and put it in the UserProfile model.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # Now we save the UserProfile model instance.
            profile.save()

            # Update our variable to tell the template registration was successful.
            registered = True

        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print(user_form.errors, profile_form.errors)

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UForm()
        profile_form = UserProfileForm()

    # Render the template depending on the context.
    return render(request, 'my_site/views/register.html',
                  {'form': [user_form, profile_form], 'registered': registered}, )


def user_login(request):
    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        username = request.POST['username']
        password = request.POST['password']

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return redirect('my_site:index')
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your Rango account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print("Invalid login details: {0}, {1}".format(username, password))
            return HttpResponse("Invalid login details supplied.")

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render(request, 'my_site/views/login.html', )


# Use the login_required() decorator to ensure only those logged in can access the view.
@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)

    # Take the user back to the homepage.
    return redirect('my_site:index')
