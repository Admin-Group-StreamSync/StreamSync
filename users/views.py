from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader

from users.models import Users


# Create your views here.

def users(request: HttpResponse):
    template = loader.get_template('myFirstTemplate.html')
    users = Users.objects.all()


    context = {
        "users": users,
    }


    return HttpResponse(template.render(context, request))