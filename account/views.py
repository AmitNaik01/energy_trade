from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.db.models import Case, When, Value, CharField
from .forms import SignUpForm, LoginForm, UserEditForm
from django.contrib.auth import authenticate, login
from django.shortcuts import render, get_object_or_404
from django.db.models.functions import TruncDay, TruncMonth
# Create your views here.
from .models import User, Proposal, Trade, Transaction, Notification
from django.contrib import messages
from django.views import View
from django.contrib.auth import logout
from django.utils import timezone
from django.db.models import Sum, Count, F
import json
from django.core.mail import EmailMultiAlternatives
from django.db.models.functions import TruncDay, TruncDate
from django.core.mail import send_mail
from django.db import models
from .utils import create_notification
from django.utils.dateparse import parse_date
from django.db.models import Q
import csv
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from datetime import timedelta, datetime
from django.utils.timezone import now
from dateutil.relativedelta import relativedelta
from decimal import Decimal



from .forms import ForgotPasswordForm, VerifyCodeForm, ResetPasswordForm
import random
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse


def index(request):
    return render(request, 'index.html')

class LogoutOnGetView(View):
    def get(self, request):
        logout(request)
        return redirect('login_view')

def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            role = form.cleaned_data.get('role')

            # Set role flags based on selected value
            if role == 'Admin':
                user.is_admin = True
            elif role == 'Seller':
                user.is_employee = True
            elif role == 'Buyer':
                user.is_customer = True

            user.save()
            return redirect('login_view')  # or wherever
    else:
        form = SignUpForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    form = LoginForm(request.POST or None)
    msg = None
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                if user.is_admin:
                    login(request, user)
                    return redirect('adminpage')
                elif user.is_customer:
                    login(request, user)
                    return redirect('buyer')
                elif user.is_employee:
                    login(request, user)
                    return redirect('seller')
                else:
                    msg = "User role not assigned. Please contact support."
            else:
                user_exists = User.objects.filter(username=username).exists()
                if user_exists:
                    msg = "Incorrect password. Please try again."
                else:
                    msg = "Username does not exist. Please check and try again."
        else:
            msg = "Incorrect Captcha!"

    return render(request, 'login.html', {'form': form, 'msg': msg})
def admin(request):
    # if not request.user.is_authenticated or not request.user.is_admin:
    #     return HttpResponseForbidden("You are not authorized to view this page.")
    return render(request, 'admin.html')

# def buyer(request):
#     return render(request,'buyer_dashboard.html')


# def seller(request):
#     return render(request,'seller-dashboard.html')
# def seller_dashboard(request):
#     if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#         # Aggregate total energy consumed and saved by all users
#         total_consumed = User.objects.aggregate(total=Sum('total_energy_consumed'))['total'] or 0
#         total_saved = User.objects.aggregate(total=Sum('total_energy_saved'))['total'] or 0
#
#         # Aggregate total energy sold and earnings where type='sell' and status='accepted' (case-insensitive)
#         total_sold = Proposal.objects.filter(
#             type__iexact='sell',
#             status__iexact='accepted'
#         ).aggregate(total=Sum('energy_ask'))['total'] or 0
#
#         # Total earnings from those sales
#         earnings = Proposal.objects.filter(
#             type__iexact='sell',
#             status__iexact='accepted'
#         ).aggregate(total=Sum('amount'))['total'] or 0
#
#         # Example static weekly data for charts (you can replace with dynamic queries)
#         weekly_data = {
#             'labels': ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'],
#             'consumed': [1500, 1000, 1200, 1100, 1300, 800, 900],
#             'saved': [200, 150, 300, 100, 180, 120, 130],
#         }
#
#         # Example static monthly revenue data for charts
#         monthly_data = {
#             'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
#             'revenue': [800, 1200, 950, 1100, 1288],
#         }
#
#         # Fetch last 5 sell proposals (trades) ordered by creation date descending
#         trades = Proposal.objects.filter(type__iexact='sell').order_by('-created_at')[:5]
#
#         recent_trades = []
#         for trade in trades:
#             user = trade.user
#             recent_trades.append({
#                 'name': user.first_name or user.username,
#                 'email': user.email,
#                 'trade': f'Sold - {trade.energy_ask} kWh',
#                 'amount': f'₹{trade.amount}',
#             })
#
#         return JsonResponse({
#             'summary': {
#                 'energy_consumed': total_consumed,
#                 'energy_saved': total_saved,
#                 'energy_sold': total_sold,
#                 'earnings': earnings,
#             },
#             'weekly_energy_usage': weekly_data,
#             'monthly_revenue': monthly_data,
#             'recent_trades': recent_trades,
#         })
#
#     # For non-AJAX requests, render the dashboard template
#     return render(request, 'seller-dashboard.html')

def seller_dashboard(request):
    user = request.user

    # Summary Data
    energy_consumed = float(user.total_energy_consumed or 0)
    energy_saved = float(user.total_energy_saved or 0)

    energy_sold = Proposal.objects.filter(user=user, type='sell').aggregate(
        total=Sum('energy_ask')
    )['total'] or 0

    earnings = Proposal.objects.filter(
        user=user,
        status__iexact='Accepted'
    ).aggregate(total=Sum('amount'))['total'] or 0

    energy_sold = float(energy_sold)
    earnings = float(earnings)

    # Weekly energy stats (last 7 days) => sold & saved
    weekly_labels = []
    weekly_sold = []
    weekly_saved = []

    for i in range(6, -1, -1):
        day = now() - timedelta(days=i)
        label = day.strftime('%a')
        weekly_labels.append(label)

        # Total sold energy (energy_ask) from proposals of type 'sell' created that day
        sold = Proposal.objects.filter(
            user=user,
            type='sell',
            created_at__date=day.date()
        ).aggregate(total=Sum('energy_ask'))['total'] or 0

        # Total saved energy from 'save' transactions that day
        saved = Transaction.objects.filter(
            user=user,
            created_at__date=day.date(),
            transaction_type__iexact='save'
        ).aggregate(total=Sum('proposal__amount'))['total'] or 0

        weekly_sold.append(float(sold or 0))
        weekly_saved.append(float(saved or 0))

    # Monthly revenue (from completed proposals)
    monthly_labels = []
    monthly_revenue = []
    today = now()

    for i in range(6, -1, -1):
        month_date = today - relativedelta(months=i)
        label = month_date.strftime('%b %Y')
        monthly_labels.append(label)

        monthly_earning = Proposal.objects.filter(
            user=user,
            status__iexact='Accepted',
            created_at__year=month_date.year,
            created_at__month=month_date.month
        ).aggregate(total=Sum('amount'))['total'] or 0

        monthly_revenue.append(float(monthly_earning or 0))

    # Recent trades (last 5)
    trades = Trade.objects.filter(
        seller=user
    ).select_related('buyer', 'proposal').order_by('-created_at')[:5]

    recent_trades = [
        {
            'name': f"{trade.buyer.username}",
            'email': trade.buyer.email,
            'trade': 'Sold',
            'amount': f"₹{float(trade.proposal.amount):.2f}"
        }
        for trade in trades
    ]

    context = {
        'summary': {
            'energy_consumed': energy_consumed,
            'energy_saved': energy_saved,
            'energy_sold': energy_sold,
            'earnings': earnings,
        },
        'weekly': {
            'labels': weekly_labels,
            'sold': weekly_sold,
            'saved': weekly_saved
        },
        'monthly': {
            'labels': monthly_labels,
            'revenue': monthly_revenue
        },
        'recent_trades': recent_trades
    }

    print("Dashboard context data:", context)

    return render(request, 'seller-dashboard.html', context)
# def buyer_dashboard(request):
#     if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#         # Aggregate total energy consumed and saved by all users
#         total_consumed = User.objects.aggregate(total=Sum('total_energy_consumed'))['total'] or 0
#         total_saved = User.objects.aggregate(total=Sum('total_energy_saved'))['total'] or 0
#
#         # Aggregate total energy bought and spending where type='buy' and status='accepted' (case-insensitive)
#         total_bought = Proposal.objects.filter(
#             type__iexact='buy',
#             status__iexact='accepted'
#         ).aggregate(total=Sum('energy_ask'))['total'] or 0
#
#         spending = Proposal.objects.filter(
#             type__iexact='buy',
#             status__iexact='accepted'
#         ).aggregate(total=Sum('amount'))['total'] or 0
#
#         # Example static weekly data for charts (replace with dynamic if needed)
#         weekly_data = {
#             'labels': ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'],
#             'consumed': [1600, 1100, 1250, 1150, 1400, 900, 1000],
#             'saved': [180, 130, 290, 90, 170, 100, 110],
#         }
#
#         # Example static monthly revenue data for charts (can be replaced)
#         monthly_data = {
#             'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
#             'revenue': [600, 1000, 870, 1050, 1200],
#         }
#
#         # Fetch last 5 buy proposals (trades) ordered by creation date descending
#         trades = Proposal.objects.filter(type__iexact='buy').order_by('-created_at')[:5]
#
#         recent_trades = []
#         for trade in trades:
#             user = trade.user
#             recent_trades.append({
#                 'name': user.first_name or user.username,
#                 'email': user.email,
#                 'trade': f'Bought - {trade.energy_ask} kWh',
#                 'amount': f'₹{trade.amount}',
#             })
#
#         return JsonResponse({
#             'summary': {
#                 'energy_consumed': total_consumed,
#                 'energy_saved': total_saved,
#                 'energy_bought': total_bought,
#                 'spending': spending,
#             },
#             'weekly_energy_usage': weekly_data,
#             'monthly_revenue': monthly_data,
#             'recent_trades': recent_trades,
#         })
#
#     return render(request, 'buyer_dashboard.html')

from collections import defaultdict
def buyer_dashboard(request):
    user = request.user

    # Summary Data
    summary = {
        'energy_consumed': user.total_energy_consumed,
        'energy_saved': user.total_energy_saved,
        'energy_bought': Trade.objects.filter(buyer=user).count(),
        'total_spent': Trade.objects.filter(buyer=user).aggregate(total=Sum('proposal__amount'))['total'] or 0
    }

    # Weekly Stats
    today = datetime.today().date()
    start_of_week = today - timedelta(days=today.weekday())
    weekly_labels = []
    weekly_bought = []
    weekly_saved = []

    for i in range(7):
        day = start_of_week + timedelta(days=i)
        label = day.strftime('%a')
        weekly_labels.append(label)

        bought = Trade.objects.filter(buyer=user, created_at__date=day).aggregate(total=Sum('proposal__energy_ask'))['total'] or 0
        saved = user.total_energy_saved / 7  # or compute per day if available

        weekly_bought.append(float(bought))
        weekly_saved.append(float(saved))

    # Monthly Spending (last 6 months)
    monthly_data = defaultdict(float)
    for i in range(6):
        month = (today.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        label = month.strftime('%b %Y')
        amount = Trade.objects.filter(
            buyer=user,
            created_at__month=month.month,
            created_at__year=month.year
        ).aggregate(total=Sum('proposal__amount'))['total'] or 0
        monthly_data[label] = float(amount)

    monthly_labels = list(reversed(list(monthly_data.keys())))
    monthly_spent = list(reversed(list(monthly_data.values())))

    # Recent Trades
    recent_trades = Trade.objects.filter(buyer=user).order_by('-created_at')[:5]
    recent_data = []
    for trade in recent_trades:
        seller = trade.seller
        recent_data.append({
            'name':  f"{trade.seller.username}",
            'email': seller.email,
            'trade': f"{trade.proposal.energy_ask}",
            'amount': f"{trade.proposal.amount}"
        })

    context = {
        'summary': summary,
        'weekly': {
            'labels': weekly_labels,
            'bought': weekly_bought,
            'saved': weekly_saved
        },
        'monthly': {
            'labels': monthly_labels,
            'spent': monthly_spent
        },
        'recent_trades': recent_data
    }

    return render(request, 'buyer_dashboard.html', context)
def user_list(request):
    users = User.objects.all()  # fetch all users
    return render(request, 'user_list.html', {'users': users})

def user_details(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'admin-user-details.html', {'user': user})

def admin_profile_details(request):
    user = request.user
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('admin_profile')  # Use the correct URL name
    else:
        form = UserEditForm(instance=user)
    return render(request, 'admin_profile_details.html', {'form': form, 'user': user})

def buyer_profile_details(request):
    user = request.user
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('buyer_profile')  # Use the correct URL name
    else:
        form = UserEditForm(instance=user)
    return render(request, 'buyer_profile_details.html', {'form': form, 'user': user})


def seller_profile_details(request):
    user = request.user
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('seller_profile')  # Use the correct URL name
    else:
        form = UserEditForm(instance=user)
    return render(request, 'seller_profile_details.html', {'form': form, 'user': user})

def edit_user_details(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = UserEditForm(instance=user)

    return render(request, 'edit_user_details.html', {'form': form, 'user': user})



def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('user_list')

def transaction_page(request):
    return render(request, 'transaction.html')

def energyanalytic_page(request):
    return render(request, 'energyanalytic.html')

def notification_page(request):
    notifications = Notification.objects.all().order_by('-created_at')
    return render(request, 'notification.html', {'notifications': notifications})





def report_page(request):
    # Total sales metrics
    total_sales_energy = Proposal.objects.aggregate(total_energy=Sum('energy_ask'))['total_energy'] or 0
    total_sales_amount =Proposal.objects.aggregate(total_amount=Sum('amount'))['total_amount'] or 0
    total_sellers = User.objects.filter(is_customer=False).count()

    # Daily sales data (last 10 days)
    recent_sales_data = (
        Proposal.objects
        .annotate(day=TruncDay('created_at'))
        .values('day')
        .annotate(daily_total=Sum('amount'))
        .order_by('-day')[:10][::-1]
    )
    daily_sales_labels = [item['day'].strftime('%Y-%m-%d') for item in recent_sales_data]
    daily_sales_values = [float(item['daily_total'] or 0) for item in recent_sales_data]

    # Monthly sales data (last 6 months)
    monthly_sales_data = (
        Proposal.objects
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(monthly_total=Sum('amount'))
        .order_by('-month')[:6][::-1]
    )
    monthly_labels = [item['month'].strftime('%b %Y') for item in monthly_sales_data]
    monthly_values = [float(item['monthly_total'] or 0) for item in monthly_sales_data]

    # Top 5 sellers by revenue
    top_sellers_data = (
        Proposal.objects
        .values(seller_name=F('user__first_name'))
        .annotate(revenue=Sum('amount'))
        .order_by('-revenue')[:5]
    )
    top_sellers_names = [item['seller_name'] or "Unknown" for item in top_sellers_data]
    top_sellers_revenue = [float(item['revenue'] or 0) for item in top_sellers_data]

    # Recent sales (last 10)
    recent_sales = (
        Proposal.objects
        .select_related('user')
        .order_by('-created_at')[:10]
    )
    recent_sales_data = [{
        'date': sale.created_at.strftime('%Y-%m-%d'),
        'seller': sale.user.first_name,
        'energy': sale.energy_ask,
        'amount': float(sale.amount)
    } for sale in recent_sales]

    context = {
        'total_sales_energy': total_sales_energy,
        'total_sales_amount': float(total_sales_amount),
        'total_sellers': total_sellers,
        'daily_sales_labels': daily_sales_labels,
        'daily_sales_values': daily_sales_values,
        'monthly_labels': monthly_labels,
        'monthly_values': monthly_values,
        'top_sellers_names': top_sellers_names,
        'top_sellers_revenue': top_sellers_revenue,
        'recent_sales': recent_sales_data,
    }

    return render(request, 'report.html', context)
def systemsetting_page(request):
    return render(request, 'systemsetting.html')

def buyer_proposals_for_seller(request):
    # Get all active BUY proposals except those by the current user (seller)
    buyer_proposals = Proposal.objects.filter(type='BUY', status='Active').exclude(user=request.user)

    return render(request, 'seller_proposal.html', {
        'proposals': buyer_proposals,
        'user': request.user,
    })


def seller_proposals_for_buyer(request):
    seller_proposals = Proposal.objects.filter(type='SELL', status='Active').exclude(user=request.user)
    return render(request, 'buyer_proposal.html', {
        'proposals': seller_proposals,
        'user': request.user,
    })

def your_proposals_seller(request):
    your_proposals_seller = Proposal.objects.filter(user=request.user, type='SELL') \
        .order_by(
            # Prioritize status 'Active' by sorting using a conditional expression
            models.Case(
                models.When(status='Active', then=0),
                default=1,
                output_field=models.IntegerField()
            ),
            '-created_at'  # Optional: latest created proposals on top
        )
    return render(request, 'your_proposal_seller.html', {'proposals': your_proposals_seller})

def your_proposals_buyer(request):
    your_proposals_buyer = Proposal.objects.filter(user=request.user, type='BUY') \
        .order_by(
            models.Case(
                models.When(status='Active', then=0),
                default=1,
                output_field=models.IntegerField()
            ),
            '-created_at'
        )
    return render(request, 'your_proposal_buyer.html', {'proposals': your_proposals_buyer})


def create_buyer_proposal(request):
    if request.method == 'POST':


        energy_ask = request.POST.get('energy_ask')
        amount = request.POST.get('amount')
        description = request.POST.get('description')

        # Prevent duplicate active proposals
        # if Proposal.objects.filter(user=request.user, type='BUY', status='Active').exists():
        #     messages.warning(request, "You already have an active buy proposal.")
        #     return redirect('seller_proposals_for_buyer')

        # Create new buyer proposal
        proposal = Proposal.objects.create(
            user=request.user,
            type='BUY',
            energy_ask=energy_ask,
            amount=amount,
            description=description,
            status='Active',
        )

        # Notify all sellers about new buyer proposal
        sellers = User.objects.filter(role='Seller')
        for seller in sellers:
            Notification.objects.create(
                user=seller,
                type='buy_proposal_created',
                message=f"New buy proposal created by {request.user.username}.",
                data={
                    'proposal_id': str(proposal.id),
                    'energy_ask': proposal.energy_ask,
                    'amount': proposal.amount,
                    'description': proposal.description,
                    'buyer': request.user.username
                }
            )

        messages.success(request, "Buy proposal created successfully.")
        return redirect('seller_proposals_for_buyer')

    return redirect('seller_proposals_for_buyer')

def create_seller_proposal(request):
    if request.method == 'POST':
        energy_ask = float(request.POST.get('energy_ask', 0))
        amount = float(request.POST.get('amount', 0))
        description = request.POST.get('description', '')
        user = request.user

        # Check if user has enough energy
        if energy_ask > user.total_energy_saved:
            messages.error(request, f"{user.username}, insufficient energy. You only have {user.total_energy_saved:.2f} kWh available.")

            return redirect('buyer_proposals_for_seller')

        # Create new sell proposal
        proposal = Proposal.objects.create(
            user=user,
            type='SELL',
            energy_ask=energy_ask,
            amount=amount,
            description=description,
            status='Active',
        )

        # Deduct energy from user account
        user.total_energy_saved -= energy_ask
        user.save()

        # Notify all buyers
        buyers = User.objects.filter(role='Buyer')
        for buyer in buyers:
            Notification.objects.create(
                user=buyer,
                type='sell_proposal_created',
                message=f"New Praposal, {user.username} Want to Sell the Energy.",
                data={
                    'proposal_id': str(proposal.id),
                    'energy_ask': proposal.energy_ask,
                    'amount': proposal.amount,
                    'description': proposal.description,
                    'seller': user.username
                }
            )

        messages.success(request, "Sell proposal created successfully.")
        return redirect('buyer_proposals_for_seller')

    return redirect('buyer_proposals_for_seller')

def edit_seller_proposal(request, proposal_id):
    proposal = get_object_or_404(Proposal, id=proposal_id, user=request.user)

    if request.method == 'POST':
        try:
            energy_ask = float(request.POST.get('energy_ask'))
            amount = float(request.POST.get('amount'))
            description = request.POST.get('description', '').strip()
        except (TypeError, ValueError):
            messages.error(request, "Invalid input. Please enter valid numbers for energy and amount.")
            return redirect('your_proposals_seller')

        old_energy_ask = float(proposal.energy_ask)
        current_energy_saved = float(request.user.total_energy_saved)

        # Calculate difference: positive means user reduced ask, negative means user increased ask
        energy_diff = old_energy_ask - energy_ask

        print(f"POSTed energy_ask: {energy_ask}")
        print(f"Old energy_ask: {old_energy_ask}")
        print(f"Energy difference: {energy_diff}")
        print(f"Current energy saved before update: {current_energy_saved}")

        if energy_diff < 0:
            # User increased ask -> check if enough energy saved
            if abs(energy_diff) >= current_energy_saved:
                messages.error(request, f"Insufficient energy. You only have {current_energy_saved:.2f} kWh.")
                return redirect('your_proposals_seller')
            # Subtract the extra energy asked from saved energy
            current_energy_saved -= abs(energy_diff)
        else:
            # User decreased ask -> add back the difference to saved energy
            current_energy_saved += energy_diff

        print(f"Updated energy saved: {current_energy_saved}")

        # Save updated energy saved to user profile
        request.user.total_energy_saved = current_energy_saved
        request.user.save()
        request.user.refresh_from_db()
        print(f"Energy saved after refresh: {request.user.total_energy_saved}")

        # Update proposal with new values
        proposal.energy_ask = energy_ask
        proposal.amount = amount
        proposal.description = description
        proposal.save()

        messages.success(request, "Proposal updated successfully.")
        return redirect('your_proposals_seller')

    # GET request - render form with existing proposal data
    return render(request, 'edit_your_proposal_seller.html', {'proposal': proposal})

def edit_buyer_proposal(request, proposal_id):
    # Fetch the proposal by ID
    proposal = get_object_or_404(Proposal, id=proposal_id, user_id=request.user.id)

    # If form is submitted (POST method)
    if request.method == 'POST':
        energy_ask = request.POST.get('energy_ask')
        amount = request.POST.get('amount')
        description = request.POST.get('description')

        # Update the proposal object
        proposal.energy_ask = energy_ask
        proposal.amount = amount
        proposal.description = description
        proposal.save()

        # Redirect to a success page or buyer dashboard
        return redirect('your_proposals_buyer')  # Replace with your actual success URL name

    # Render the form with current proposal data
    return render(request, 'edit_your_proposal_buyer.html', {
        'proposal': proposal,
        'user': request.user,
    })
def delete_buyer_proposal(request, proposal_id):
    proposal = get_object_or_404(Proposal, id=proposal_id, user_id=request.user.id)
    proposal.delete()
    return redirect('your_proposals_buyer')

def delete_seller_proposal(request, proposal_id):
    if request.method == "POST":
        proposal = get_object_or_404(Proposal, id=proposal_id, user=request.user)

        current_energy_saved = float(request.user.total_energy_saved)
        energy_ask = float(proposal.energy_ask)
        updated_energy_saved = current_energy_saved + energy_ask

        request.user.total_energy_saved = updated_energy_saved
        request.user.save()

        proposal.delete()

        messages.success(request, "Proposal deleted and energy restored successfully.")
        return redirect('your_proposals_seller')
    else:
        messages.error(request, "Invalid request method.")
        return redirect('your_proposals_seller')
def seller_process_trade(request):
    if request.method == 'POST':
        proposal_id = request.POST.get('proposal_id')
        action = request.POST.get('action')

        proposal = get_object_or_404(Proposal, id=proposal_id)
        buyer = proposal.user
        seller = request.user

        if action == 'accept':
            # Check if seller has enough energy
            if float(proposal.energy_ask) > seller.total_energy_saved:
                messages.error(request, f"Insufficient energy. {seller.username}, you only have {seller.total_energy_saved:.2f} kWh available.")
                return redirect('buyer_proposals_for_seller')

            # Deduct energy from seller
            seller.total_energy_saved -= float(proposal.energy_ask)
            seller.save()

            # Add energy to buyer
            buyer.total_energy_saved += float(proposal.energy_ask)
            buyer.save()

            # 1. Update proposal
            proposal.status = 'Accepted'
            proposal.save()

            # 2. Create Transaction for seller
            Transaction.objects.create(
                user=seller,
                proposal=proposal,
                transaction_type='SELL',
                status='Completed',
                created_at=timezone.now()
            )

            # 3. Create Trade record
            Trade.objects.create(
                buyer=buyer,
                seller=seller,
                proposal=proposal,
                status='Completed',
                created_at=timezone.now()
            )

            # 4. Create notifications for both buyer and seller
            Notification.objects.create(
                user=buyer,
                type='trade_accepted',
                message=f"Proposal was accepted by {seller.username}.",
                data={
                    'proposal_id': str(proposal.id),
                    'energy_ask': proposal.energy_ask,
                    'amount': proposal.amount,
                    'seller': seller.username
                }
            )

            Notification.objects.create(
                user=seller,
                type='trade_confirmed',
                message=f"{request.user.username}, accepted the proposal from {buyer.username}.",
                data={
                    'proposal_id': str(proposal.id),
                    'energy_ask': proposal.energy_ask,
                    'amount': proposal.amount,
                    'buyer': buyer.username
                }
            )

            messages.success(request, "Trade accepted and recorded successfully.")

        elif action == 'reject':
            proposal.status = 'Rejected'
            proposal.save()

            # Notify the buyer about rejection
            Notification.objects.create(
                user=buyer,
                type='trade_rejected',
                message=f"{request.user.username}, proposal was rejected by {seller.username}.",
                data={
                    'proposal_id': str(proposal.id),
                    'energy_ask': proposal.energy_ask,
                    'amount': proposal.amount,
                    'seller': seller.username
                }
            )

            messages.warning(request, "Trade was rejected.")

        return redirect('buyer_proposals_for_seller')

def buyer_process_trade(request):
    if request.method == 'POST':
        proposal_id = request.POST.get('proposal_id')
        action = request.POST.get('action')

        proposal = get_object_or_404(Proposal, id=proposal_id)
        buyer = request.user
        seller = proposal.user

        if action == 'accept':
            # 1. Update proposal
            proposal.status = 'Accepted'
            proposal.save()

            # Add energy_ask to buyer's total_energy_saved
            buyer.total_energy_saved += float(proposal.energy_ask)
            buyer.save()

            # 2. Create Transaction for buyer
            Transaction.objects.create(
                user=buyer,
                proposal=proposal,
                transaction_type='BUY',
                status='Completed',
                created_at=timezone.now()
            )

            # 3. Create Trade record
            Trade.objects.create(
                buyer=buyer,
                seller=seller,
                proposal=proposal,
                status='Completed',
                created_at=timezone.now()
            )

            # 4. Create notifications for both buyer and seller
            Notification.objects.create(
                user=seller,
                type='trade_accepted',
                message=f"Proposal was accepted by  {seller.username}.",
                data={
                    'proposal_id': str(proposal.id),
                    'energy_ask': proposal.energy_ask,
                    'amount': proposal.amount,
                    'buyer': buyer.username
                }
            )

            Notification.objects.create(
                user=buyer,
                type='trade_confirmed',
                message=f"{request.user.username}, accepted the proposal from {seller.username}.",
                data={
                    'proposal_id': str(proposal.id),
                    'energy_ask': proposal.energy_ask,
                    'amount': proposal.amount,
                    'seller': seller.username
                }
            )

            messages.success(request, "Trade accepted successfully.")

        elif action == 'reject':
            proposal.status = 'Rejected'
            proposal.save()

            # 5. Create rejection notification for seller
            Notification.objects.create(
                user=seller,
                type='trade_rejected',
                message=f"{request.user.username}, proposal was rejected by {buyer.username}.",
                data={
                    'proposal_id': str(proposal.id),
                    'energy_ask': proposal.energy_ask,
                    'amount': proposal.amount,
                    'buyer': buyer.username
                }
            )

            messages.warning(request, "Trade rejected.")

        return redirect('seller_proposals_for_buyer')


def seller_notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'seller_notifications.html', {'notifications': notifications})


def buyer_notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'buyer_notifications.html', {'notifications': notifications})
def buyer_transactions_view(request):
    search_query = request.GET.get('search', '').strip()
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    # Read rows per page from GET param, default 10, max 100 for safety
    try:
        rows_per_page = int(request.GET.get('rows_per_page', 10))
        if rows_per_page > 100:
            rows_per_page = 100
    except ValueError:
        rows_per_page = 10

    # Filter trades where the current user is the buyer
    trades = Trade.objects.filter(buyer=request.user).select_related('buyer', 'seller', 'proposal')

    # Apply search filter
    if search_query:
        trades = trades.filter(
            Q(seller__username__icontains=search_query) |
            Q(buyer__email__icontains=search_query) |
            Q(id__icontains=search_query)
        )

    # Apply date filter
    if start_date:
        trades = trades.filter(created_at__date__gte=start_date)
    if end_date:
        trades = trades.filter(created_at__date__lte=end_date)

    trades = trades.order_by('-created_at')

    # Add display type for each trade (flip SELL and BUY roles if needed)
    for trade in trades:
        if trade.proposal.type == 'BUY':
            trade.display_type = f"Accepted & Sold by {trade.seller.username}"
        elif trade.proposal.type == 'SELL':
            trade.display_type = f"Accepted & Bought by {trade.buyer.username}"
        else:
            trade.display_type = trade.proposal.type

    paginator = Paginator(trades, rows_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
        'rows_per_page': rows_per_page,
    }

    return render(request, 'buyer_transaction.html', context)


from django.core.paginator import Paginator


def seller_transactions_view(request):
    search_query = request.GET.get('search', '').strip()
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    # Read rows per page from GET param, default 10, max 100 for safety
    try:
        rows_per_page = int(request.GET.get('rows_per_page', 10))
        if rows_per_page > 100:
            rows_per_page = 100
    except ValueError:
        rows_per_page = 10

    trades = Trade.objects.filter(seller=request.user).select_related('buyer', 'seller', 'proposal')

    # Apply search filter
    if search_query:
        trades = trades.filter(
            Q(buyer__username__icontains=search_query) |
            Q(seller__email__icontains=search_query) |
            Q(id__icontains=search_query)
        )

    # Apply date filter
    if start_date:
        trades = trades.filter(created_at__date__gte=start_date)
    if end_date:
        trades = trades.filter(created_at__date__lte=end_date)

    trades = trades.order_by('-created_at')

    # Add display type for each trade
    for trade in trades:
        if trade.proposal.type == 'SELL':
            trade.display_type = f"Accepted & Bought by {trade.buyer.username}"
        elif trade.proposal.type == 'BUY':
            trade.display_type = f"Accepted & Sold by {trade.seller.username}"
        else:
            trade.display_type = trade.proposal.type

    paginator = Paginator(trades, rows_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Pass rows_per_page so the template can keep it selected
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
        'rows_per_page': rows_per_page,
    }

    # # AJAX request (optional partial rendering)
    # if request.headers.get('x-requested-with') == 'XMLHttpRequest':
    #     return render(request, 'transaction_table.html', context)

    return render(request, 'seller_transaction.html', context)


def admin_transactions_view(request):
    search_query = request.GET.get('search', '').strip()
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    # Read rows per page from GET param, default 10, max 100 for safety
    try:
        rows_per_page = int(request.GET.get('rows_per_page', 10))
        if rows_per_page > 100:
            rows_per_page = 100
    except ValueError:
        rows_per_page = 10

    # Start with all trades, select related to reduce queries
    trades = Trade.objects.select_related('buyer', 'seller', 'proposal')

    # Apply search filter on buyer, seller usernames and trade id
    if search_query:
        trades = trades.filter(
            Q(buyer__username__icontains=search_query) |
            Q(seller__username__icontains=search_query) |
            Q(id__icontains=search_query)
        )

    # Apply date filters if provided
    if start_date:
        trades = trades.filter(created_at__date__gte=start_date)
    if end_date:
        trades = trades.filter(created_at__date__lte=end_date)

    # Order by newest first
    trades = trades.order_by('-created_at')

    # Annotate each trade with display_type label
    trades = trades.annotate(
        display_type=Case(
            When(proposal__type='BUY', then=Value('BUY - Accepted & Sold by Seller')),
            When(proposal__type='SELL', then=Value('SELL - Accepted & Bought by Buyer')),
            default=Value('Unknown'),
            output_field=CharField(),
        )
    )

    # Paginate the results
    paginator = Paginator(trades, rows_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
        'rows_per_page': rows_per_page,
    }

    return render(request, 'admin_transactions.html', context)





 # Replace 'yourapp' with your app name

def dashboard_view(request):
    # Permission check (only admin users)
    # if not request.user.is_authenticated or not request.user.is_admin:
    #     return render(request, '403.html', status=403)

    today = datetime.today().date()

    # Summary Stats
    total_users = User.objects.count()
    total_energy_consumed = Proposal.objects.aggregate(total=Sum('energy_ask'))['total'] or 0
    total_energy_saved = User.objects.aggregate(total=Sum('total_energy_saved'))['total'] or 0
    total_earning = Proposal.objects.aggregate(total=Sum('amount'))['total'] or 0

    unique_buyers = User.objects.filter(role='customer').count()
    unique_sellers = User.objects.filter(role='seller').count()

    summary = {
        'users': total_users,
        'energy_consumed': total_energy_consumed,
        'energy_saved': total_energy_saved,
        'earning': total_earning,
    }

    # Trades per Day (Last 10 Days)
    trades_per_day_qs = (
        Trade.objects
        .annotate(day=TruncDay('created_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('-day')[:10]
    )
    trades_per_day_qs = list(reversed(trades_per_day_qs))  # oldest first
    daily_trade_labels = [item['day'].strftime('%b %d') for item in trades_per_day_qs]
    daily_trade_counts = [item['count'] for item in trades_per_day_qs]

    # Monthly Earnings (last 6 months)
    monthly_data = defaultdict(float)
    for i in range(5, -1, -1):  # past 6 months in chronological order
        month = (today.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        label = month.strftime('%b %Y')
        total = Proposal.objects.filter(
            created_at__year=month.year,
            created_at__month=month.month
        ).aggregate(total=Sum('amount'))['total'] or 0
        monthly_data[label] = float(total)

    monthly_earning_labels = list(monthly_data.keys())
    monthly_earning_values = list(monthly_data.values())

    # Recent Trades (Last 5)
    recent_trades_qs = Trade.objects.select_related('buyer', 'seller', 'proposal').order_by('-created_at')[:5]
    recent_trades = []
    for trade in recent_trades_qs:
        recent_trades.append({
            'date': trade.created_at.strftime('%Y-%m-%d'),
            'buyer': f"{trade.buyer.first_name} {trade.buyer.last_name}",
            'seller': f"{trade.seller.first_name} {trade.seller.last_name}",
            'energy': trade.proposal.energy_ask,
            'amount': trade.proposal.amount,
        })

    monthly_energy = defaultdict(float)
    monthly_earning = defaultdict(float)
    for i in range(5, -1, -1):  # past 6 months in chronological order
        month = (today.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        label = month.strftime('%b %Y')

        proposals = Proposal.objects.filter(
            created_at__year=month.year,
            created_at__month=month.month
        )

        total_energy = proposals.aggregate(total=Sum('energy_ask'))['total'] or 0
        total_amount = proposals.aggregate(total=Sum('amount'))['total'] or 0

        monthly_energy[label] = float(total_energy)
        monthly_earning[label] = float(total_amount)

    monthly_labels = list(monthly_energy.keys())
    monthly_energy_values = list(monthly_energy.values())
    monthly_earning_values = list(monthly_earning.values())

    context = {
        'summary': summary,
        'daily_trade_labels': json.dumps(daily_trade_labels),
        'daily_trade_counts': json.dumps(daily_trade_counts),
        'monthly_earning_labels': json.dumps(monthly_earning_labels),
        'monthly_earning_values': json.dumps(monthly_earning_values),
        'recent_trades': recent_trades,
        'unique_buyers': unique_buyers,
        'unique_sellers': unique_sellers,
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_energy_values': json.dumps(monthly_energy_values),  # For bars
        'monthly_earning_values': json.dumps(monthly_earning_values),  # For line

    }

    return render(request, 'admin.html', context)

def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                code = str(random.randint(100000, 999999))
                user.reset_code = code
                user.save()
                message = f"""
                Hello,

                We received a request to reset the password for your account associated with this email address.

                Your One-Time Password (OTP) reset code is: {code}

                If you did not request a password reset, please ignore this email.

                Thank you,
                Support Team
                """
                send_mail(
                    'Password Reset Code',
                    message,
                    'gestione-cer@sbamsas.eu',
                    [email],
                    fail_silently=False,
                )
                request.session['reset_email'] = email
                messages.success(request, 'Reset code sent to your email')
                return redirect('verify_code')
            except User.DoesNotExist:
                messages.error(request, 'Email not found')
        else:
            messages.error(request, 'Invalid input. Please try again.')
    else:
        form = ForgotPasswordForm()

    return render(request, 'forgot_password.html', {'form': form})



def verify_code_view(request):
    if request.method == 'POST':
        email = request.session.get('reset_email')
        code = request.POST.get('code')
        try:
            user = User.objects.get(email=email)
            if user.reset_code == code:
                messages.success(request, 'Code verified! Please reset your password.')
                return redirect('reset_password')
            else:
                messages.error(request, 'Invalid code')
        except User.DoesNotExist:
            messages.error(request, 'Session expired. Please start over.')
            return redirect('forgot_password')
    return render(request, 'verify_code.html')


def reset_password_view(request):
    if request.method == 'POST':
        email = request.session.get('reset_email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        if password != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('reset_password')

        try:
            user = User.objects.get(email=email)
            user.set_password(password)
            user.reset_code = ''
            user.save()
            messages.success(request, 'Password reset successful! You can now log in.')
            # Optionally clear session here
            request.session.pop('reset_email', None)
            return redirect('login_view')  # Replace 'login' with your login URL name
        except User.DoesNotExist:
            messages.error(request, 'Session expired. Please start over.')
            return redirect('forgot_password')

    return render(request, 'reset_password.html')



def seller_buyers_view(request):
    seller = request.user

    trades = Trade.objects.filter(seller_id=seller.id)
    buyer_ids = trades.values_list('buyer_id', flat=True).distinct()

    buyers_data = []
    for buyer_id in buyer_ids:
        buyer = User.objects.get(id=buyer_id)
        total_energy_sold = trades.filter(buyer_id=buyer_id).aggregate(
            total_energy=Sum('proposal__energy_ask')
        )['total_energy'] or 0.0

        buyers_data.append({
            'name': buyer.username,
            'email': buyer.email,
            'address': buyer.address,
            'contact_no': buyer.contact_no,
            'status': buyer.status,
            'energy_sold': total_energy_sold
        })

    context = {
        'buyers_data': buyers_data
    }
    return render(request, 'seller_buyer_list.html', context)

def buyer_seller_list_view(request):
    buyer = request.user
    search_query = request.GET.get('search', '').strip()

    trades = Trade.objects.filter(buyer_id=buyer.id)
    seller_ids = trades.values_list('seller_id', flat=True).distinct()

    sellers_data = []
    for seller_id in seller_ids:
        seller = User.objects.get(id=seller_id)
        total_energy = trades.filter(seller_id=seller_id).aggregate(total_sold=models.Sum('proposal__amount'))['total_sold'] or 0

        sellers_data.append({
            'name': seller.username,
            'email': seller.email,
            'address': seller.address,
            'energy_bought': total_energy,
            'contact_no': seller.contact_no,
            'status': seller.status,
        })

    # Filter sellers_data in Python if search_query is present
    if search_query:
        sellers_data = [
            seller for seller in sellers_data
            if search_query.lower() in seller['name'].lower()
            or search_query.lower() in seller['email'].lower()
            or search_query.lower() in seller['address'].lower()
        ]

    context = {
        'sellers_data': sellers_data,
        'search_query': search_query,
    }
    return render(request, 'buyer_seller_list.html', context)

def download_invoice(request, trade_id):
    trade = get_object_or_404(Trade, pk=trade_id)
    proposal = trade.proposal

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=invoice_{trade.id}.pdf'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Header section with green theme
    p.setFillColor(colors.green)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(200, height - 60, f" Energy Trade Invoice")

    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.darkgreen)
    p.drawString(100, height - 100, f"Invoice ID: {trade.id}")

    # Draw a decorative green rectangle background
    # p.setFillColor(colors.lightgreen)
    # p.rect(80, height - 130, 450, 30, fill=True, stroke=False)

    # Back to default text color
    p.setFillColor(colors.black)
    p.setFont("Helvetica", 12)

    details = [
        ("Buyer:", f"{trade.buyer.username} ({trade.buyer.email})"),
        ("Seller:", f"{trade.seller.username} ({trade.seller.email})"),
        ("Proposal Type:", proposal.type),
        ("Proposal Description:", proposal.description),
        ("Energy Traded (kWh):", f"{proposal.energy_ask}"),
        ("Trade Amount (Є):", f"{proposal.amount:.2f}"),
        ("Status:", trade.status),
        ("Trade Date:", trade.created_at.strftime('%b %d, %Y, %I:%M %p')),
    ]

    y = height - 150
    for label, value in details:
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, y, label)
        p.setFont("Helvetica", 12)
        p.drawString(250, y, str(value))
        y -= 25

    # Footer
    p.setFillColor(colors.darkgray)
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(100, 80, "This invoice is auto-generated by the Energy Trade Platform.")
    p.drawString(100, 65, "Thank you for supporting clean energy.")

    p.showPage()
    p.save()

    return response

def export_trades_csv(request):
    trades = Trade.objects.select_related('buyer', 'seller', 'proposal').all()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="trades.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Buyer', 'Seller', 'Proposal Type', 'Description', 'Energy (kWh)', 'Amount (INR)', 'Status', 'Created At'])

    for trade in trades:
        writer.writerow([
            trade.id,
            trade.buyer.username,
            trade.seller.username,
            trade.proposal.type,
            trade.proposal.description,
            trade.proposal.energy_ask,
            trade.proposal.amount,
            trade.status,
            trade.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    return response