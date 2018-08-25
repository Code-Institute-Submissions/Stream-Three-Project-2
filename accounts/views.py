# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from accounts.forms import UserRegistrationForm, UserLoginForm
from .models import User
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.template.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from .models import User
import stripe


# Create your views here.
# >signup page view
def signup(request):
  if request.user.is_authenticated:
    return redirect(reverse('accounts:profile'))

  form = UserRegistrationForm()
  return render(request, 'accounts/form.html', {'form': form, 'title': 'Create New Account'})

# >login page view
def login(request):
  if request.user.is_authenticated:
    return redirect(reverse('accounts:profile'))

  form = UserLoginForm()
  args = {'form':form}
  args.update(csrf(request))
  args['title'] = 'Login'
  return render(request, 'accounts/form.html', args)

# >profile page view
@login_required(login_url='accounts:login') 
def profile(request):
  user = get_object_or_404(User, id=request.user.id)
  args = {}
  try:
    allTickets = Ticket.objects.all()
    tickets = Ticket.objects.filter(user=user)
    comments = Comment.objects.filter(user=user)
    votes = UpVote.objects.filter(user=user)
    args['alltickets'] = allTickets
    args['tickets'] = tickets
    args['comments'] = comments
    args['votes'] = votes
  except Exception as e:
    pass

  if user.stripe_id:
    customer = stripe.Customer.retrieve(user.stripe_id)
    if customer.subscriptions.total_count > 0 and customer.subscriptions.data[0].status == 'active':
      args['status'] = True
    else:
      args['status'] = False
    return render(request, 'accounts/profile.html',args)
  else:
    args['status'] = False
    return render(request, 'accounts/profile.html',args)

# >payments
@csrf_exempt
def payments(request):
  # pprint(repr(request.POST))
  user = get_object_or_404(User, id=request.user.id)
  try:
    #  If user is already subscribed
    if user.stripe_id:
      customer = stripe.Customer.retrieve(user.stripe_id)
      if customer.subscriptions.total_count > 0 and customer.subscriptions.data[0].plan.id == devTrackerPlan:
        return redirect(reverse('accounts:profile'))

      subscription = stripe.Subscription.create(
        customer=user.stripe_id,
        items=[{'plan': devTrackerPlan}],
      )
      
      user.sub_end = datetime.utcfromtimestamp(int(subscription.current_period_end))
    else:
      token = request.POST['stripeToken']

      customer = stripe.Customer.create(
        source=token,
        email=user.email,
      )

      user.stripe_id = customer.id
     
      subscription = stripe.Subscription.create(
        customer=user.stripe_id,
        items=[{'plan': devTrackerPlan}],
      )
    
      if subscription.status == 'active':
        user.subscription = True
      else:
        user.subscription = False
    user.save()
  except stripe.error.CardError as e:
    # Since it's a decline, stripe.error.CardError will be caught
    body = e.json_body
    err  = body.get('error', {})

    print "Status is: %s" % e.http_status
    print "Type is: %s" % err.get('type')
    print "Code is: %s" % err.get('code')
    # param is '' in this case
    print "Param is: %s" % err.get('param')
    print "Message is: %s" % err.get('message')
  except stripe.error.RateLimitError as e:
    # Too many requests made to the API too quickly
    body = e.json_body
    err  = body.get('error', {})

    print "Status is: %s" % e.http_status
    print "Type is: %s" % err.get('type')
    print "Code is: %s" % err.get('code')
    # param is '' in this case
    print "Param is: %s" % err.get('param')
    print "Message is: %s" % err.get('message')
  except stripe.error.InvalidRequestError as e:
    # Invalid parameters were supplied to Stripe's API
    body = e.json_body
    err  = body.get('error', {})

    print "Status is: %s" % e.http_status
    print "Type is: %s" % err.get('type')
    print "Code is: %s" % err.get('code')
    # param is '' in this case
    print "Param is: %s" % err.get('param')
    print "Message is: %s" % err.get('message')
  except stripe.error.AuthenticationError as e:
    # Authentication with Stripe's API failed
    # (maybe you changed API keys recently)
    body = e.json_body
    err  = body.get('error', {})

    print "Status is: %s" % e.http_status
    print "Type is: %s" % err.get('type')
    print "Code is: %s" % err.get('code')
    # param is '' in this case
    print "Param is: %s" % err.get('param')
    print "Message is: %s" % err.get('message')
  except stripe.error.APIConnectionError as e:
    # Network communication with Stripe failed
    body = e.json_body
    pprint(repr(body))
    pprint(dir(body))

    err  = body.get('error', {})

    print "Status is: %s" % e.http_status
    print "Type is: %s" % err.get('type')
    print "Code is: %s" % err.get('code')
    # param is '' in this case
    print "Param is: %s" % err.get('param')
    print "Message is: %s" % err.get('message')
  except stripe.error.StripeError as e:
    # Display a very generic error to the user, and maybe send
    # yourself an email
    body = e.json_body
    err  = body.get('error', {})

    print "Status is: %s" % e.http_status
    print "Type is: %s" % err.get('type')
    print "Code is: %s" % err.get('code')
    # param is '' in this case
    print "Param is: %s" % err.get('param')
    print "Message is: %s" % err.get('message')
  except Exception as e:
    # Something else happened, completely unrelated to Stripe
    body = e.json_body
    err  = body.get('error', {})

    print "Status is: %s" % e.http_status
    print "Type is: %s" % err.get('type')
    print "Code is: %s" % err.get('code')
    # param is '' in this case
    print "Param is: %s" % err.get('param')
    print "Message is: %s" % err.get('message')

  # Refresh profile Page
  return redirect(reverse('accounts:profile'))

def cancel_subscription(request):
  if request.method == 'POST':
    user = get_object_or_404(User, id=request.user.id)
    customer = stripe.Customer.retrieve(user.stripe_id)
    try:
      subscription = stripe.Subscription.retrieve(customer.subscriptions.data[0].id)
      subscription.delete()
      user['is_active'] = False
    except stripe.error.CardError as e:
      # Since it's a decline, stripe.error.CardError will be caught
      body = e.json_body
      err  = body.get('error', {})

      print "Status is: %s" % e.http_status
      print "Type is: %s" % err.get('type')
      print "Code is: %s" % err.get('code')
      # param is '' in this case
      print "Param is: %s" % err.get('param')
      print "Message is: %s" % err.get('message')
    except stripe.error.RateLimitError as e:
      # Too many requests made to the API too quickly
      body = e.json_body
      err  = body.get('error', {})

      print "Status is: %s" % e.http_status
      print "Type is: %s" % err.get('type')
      print "Code is: %s" % err.get('code')
      # param is '' in this case
      print "Param is: %s" % err.get('param')
      print "Message is: %s" % err.get('message')
    except stripe.error.InvalidRequestError as e:
      # Invalid parameters were supplied to Stripe's API
      body = e.json_body
      err  = body.get('error', {})

      print "Status is: %s" % e.http_status
      print "Type is: %s" % err.get('type')
      print "Code is: %s" % err.get('code')
      # param is '' in this case
      print "Param is: %s" % err.get('param')
      print "Message is: %s" % err.get('message')
    except stripe.error.AuthenticationError as e:
      # Authentication with Stripe's API failed
      # (maybe you changed API keys recently)
      body = e.json_body
      err  = body.get('error', {})

      print "Status is: %s" % e.http_status
      print "Type is: %s" % err.get('type')
      print "Code is: %s" % err.get('code')
      # param is '' in this case
      print "Param is: %s" % err.get('param')
      print "Message is: %s" % err.get('message')
    except stripe.error.APIConnectionError as e:
      # Network communication with Stripe failed
      body = e.json_body
      pprint(repr(body))
      pprint(dir(body))

      err  = body.get('error', {})

      print "Status is: %s" % e.http_status
      print "Type is: %s" % err.get('type')
      print "Code is: %s" % err.get('code')
      # param is '' in this case
      print "Param is: %s" % err.get('param')
      print "Message is: %s" % err.get('message')
    except stripe.error.StripeError as e:
      # Display a very generic error to the user, and maybe send
      # yourself an email
      body = e.json_body
      err  = body.get('error', {})

      print "Status is: %s" % e.http_status
      print "Type is: %s" % err.get('type')
      print "Code is: %s" % err.get('code')
      # param is '' in this case
      print "Param is: %s" % err.get('param')
      print "Message is: %s" % err.get('message')
    except Exception as e:
      # Something else happened, completely unrelated to Stripe
      body = e.json_body
      err  = body.get('error', {})

      print "Status is: %s" % e.http_status
      print "Type is: %s" % err.get('type')
      print "Code is: %s" % err.get('code')
      # param is '' in this case
      print "Param is: %s" % err.get('param')
      print "Message is: %s" % err.get('message')
      
  return redirect('accounts:profile')

# >settings pageview
@login_required(login_url='accounts:login')
def settings(request):
  return render(request, 'accounts/settings.html')

# >settings pageview
def delete(request):
  user = get_object_or_404(User, id=request.user.id)
  try:
    if user.stripe_id:
      customer = stripe.Customer.retrieve(user.stripe_id)
      subscription = stripe.Subscription.retrieve(customer.subscriptions.data[0].id)
      subscription.delete()
    user.delete()
  except stripe.error.CardError as e:
    # Since it's a decline, stripe.error.CardError will be caught
    body = e.json_body
    err  = body.get('error', {})

    print "Status is: %s" % e.http_status
    print "Type is: %s" % err.get('type')
    print "Code is: %s" % err.get('code')
    # param is '' in this case
    print "Param is: %s" % err.get('param')
    print "Message is: %s" % err.get('message')
  except stripe.error.RateLimitError as e:
    # Too many requests made to the API too quickly
    body = e.json_body
    err  = body.get('error', {})

    print "Status is: %s" % e.http_status
    print "Type is: %s" % err.get('type')
    print "Code is: %s" % err.get('code')
    # param is '' in this case
    print "Param is: %s" % err.get('param')
    print "Message is: %s" % err.get('message')
  except stripe.error.InvalidRequestError as e:
    # Invalid parameters were supplied to Stripe's API
    body = e.json_body
    err  = body.get('error', {})

    print "Status is: %s" % e.http_status
    print "Type is: %s" % err.get('type')
    print "Code is: %s" % err.get('code')
    # param is '' in this case
    print "Param is: %s" % err.get('param')
    print "Message is: %s" % err.get('message')
  except stripe.error.AuthenticationError as e:
    # Authentication with Stripe's API failed
    # (maybe you changed API keys recently)
    body = e.json_body
    err  = body.get('error', {})

    print "Status is: %s" % e.http_status
    print "Type is: %s" % err.get('type')
    print "Code is: %s" % err.get('code')
    # param is '' in this case
    print "Param is: %s" % err.get('param')
    print "Message is: %s" % err.get('message')
  except stripe.error.APIConnectionError as e:
    # Network communication with Stripe failed
    body = e.json_body
    pprint(repr(body))
    pprint(dir(body))

    err  = body.get('error', {})

    print "Status is: %s" % e.http_status
    print "Type is: %s" % err.get('type')
    print "Code is: %s" % err.get('code')
    # param is '' in this case
    print "Param is: %s" % err.get('param')
    print "Message is: %s" % err.get('message')
  except stripe.error.StripeError as e:
    # Display a very generic error to the user, and maybe send
    # yourself an email
    body = e.json_body
    err  = body.get('error', {})

    print "Status is: %s" % e.http_status
    print "Type is: %s" % err.get('type')
    print "Code is: %s" % err.get('code')
    # param is '' in this case
    print "Param is: %s" % err.get('param')
    print "Message is: %s" % err.get('message')
  except Exception as e:
    # Something else happened, completely unrelated to Stripe
    body = e.json_body
    err  = body.get('error', {})

    print "Status is: %s" % e.http_status
    print "Type is: %s" % err.get('type')
    print "Code is: %s" % err.get('code')
    # param is '' in this case
    print "Param is: %s" % err.get('param')
    print "Message is: %s" % err.get('message')
      
  return redirect('tracker:index')