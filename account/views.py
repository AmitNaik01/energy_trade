from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.db.models import Case, When, Value, CharField
from .forms import SignUpForm, LoginForm, UserEditForm
from django.contrib.auth import authenticate, login
from django.shortcuts import render, get_object_or_404
# Create your views here.
from .models import User, Proposal, Trade, Transaction, Notification
from django.contrib import messages
from django.views import View
from django.contrib.auth import logout
from django.utils import timezone
from django.db.models import Sum, Count
import json
from django.core.mail import EmailMultiAlternatives
from django.db.models.functions import TruncDay
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
            if user is not None and user.is_admin:
                login(request, user)
                return redirect('adminpage')
            elif user is not None and user.is_customer:
                login(request, user)
                return redirect('buyer')
            elif user is not None and user.is_employee:
                login(request, user)
                return redirect('seller')
            else:
                msg= 'invalid credentials'
        else:
            msg = 'error validating form'
    return render(request, 'login.html', {'form': form, 'msg': msg})


def admin(request):
    # if not request.user.is_authenticated or not request.user.is_admin:
    #     return HttpResponseForbidden("You are not authorized to view this page.")
    return render(request, 'admin.html')

# def buyer(request):
#     return render(request,'buyer_dashboard.html')


# def seller(request):
#     return render(request,'seller-dashboard.html')
def seller_dashboard(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Aggregate total energy consumed and saved by all users
        total_consumed = User.objects.aggregate(total=Sum('total_energy_consumed'))['total'] or 0
        total_saved = User.objects.aggregate(total=Sum('total_energy_saved'))['total'] or 0

        # Aggregate total energy sold and earnings where type='sell' and status='accepted' (case-insensitive)
        total_sold = Proposal.objects.filter(
            type__iexact='sell',
            status__iexact='accepted'
        ).aggregate(total=Sum('energy_ask'))['total'] or 0

        # Total earnings from those sales
        earnings = Proposal.objects.filter(
            type__iexact='sell',
            status__iexact='accepted'
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Example static weekly data for charts (you can replace with dynamic queries)
        weekly_data = {
            'labels': ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'],
            'consumed': [1500, 1000, 1200, 1100, 1300, 800, 900],
            'saved': [200, 150, 300, 100, 180, 120, 130],
        }

        # Example static monthly revenue data for charts
        monthly_data = {
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
            'revenue': [800, 1200, 950, 1100, 1288],
        }

        # Fetch last 5 sell proposals (trades) ordered by creation date descending
        trades = Proposal.objects.filter(type__iexact='sell').order_by('-created_at')[:5]

        recent_trades = []
        for trade in trades:
            user = trade.user
            recent_trades.append({
                'name': user.first_name or user.username,
                'email': user.email,
                'trade': f'Sold - {trade.energy_ask} kWh',
                'amount': f'₹{trade.amount}',
            })

        return JsonResponse({
            'summary': {
                'energy_consumed': total_consumed,
                'energy_saved': total_saved,
                'energy_sold': total_sold,
                'earnings': earnings,
            },
            'weekly_energy_usage': weekly_data,
            'monthly_revenue': monthly_data,
            'recent_trades': recent_trades,
        })

    # For non-AJAX requests, render the dashboard template
    return render(request, 'seller-dashboard.html')


def buyer_dashboard(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Aggregate total energy consumed and saved by all users
        total_consumed = User.objects.aggregate(total=Sum('total_energy_consumed'))['total'] or 0
        total_saved = User.objects.aggregate(total=Sum('total_energy_saved'))['total'] or 0

        # Aggregate total energy bought and spending where type='buy' and status='accepted' (case-insensitive)
        total_bought = Proposal.objects.filter(
            type__iexact='buy',
            status__iexact='accepted'
        ).aggregate(total=Sum('energy_ask'))['total'] or 0

        spending = Proposal.objects.filter(
            type__iexact='buy',
            status__iexact='accepted'
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Example static weekly data for charts (replace with dynamic if needed)
        weekly_data = {
            'labels': ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'],
            'consumed': [1600, 1100, 1250, 1150, 1400, 900, 1000],
            'saved': [180, 130, 290, 90, 170, 100, 110],
        }

        # Example static monthly revenue data for charts (can be replaced)
        monthly_data = {
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
            'revenue': [600, 1000, 870, 1050, 1200],
        }

        # Fetch last 5 buy proposals (trades) ordered by creation date descending
        trades = Proposal.objects.filter(type__iexact='buy').order_by('-created_at')[:5]

        recent_trades = []
        for trade in trades:
            user = trade.user
            recent_trades.append({
                'name': user.first_name or user.username,
                'email': user.email,
                'trade': f'Bought - {trade.energy_ask} kWh',
                'amount': f'₹{trade.amount}',
            })

        return JsonResponse({
            'summary': {
                'energy_consumed': total_consumed,
                'energy_saved': total_saved,
                'energy_bought': total_bought,
                'spending': spending,
            },
            'weekly_energy_usage': weekly_data,
            'monthly_revenue': monthly_data,
            'recent_trades': recent_trades,
        })

    return render(request, 'buyer_dashboard.html')
def user_list(request):
    users = User.objects.all()  # fetch all users
    return render(request, 'user_list.html', {'users': users})

def user_details(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'admin-user-details.html', {'user': user})

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
    return render(request, 'notification.html')

def report_page(request):
    return render(request, 'report.html')

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
    your_proposals_seller = Proposal.objects.filter(user=request.user, type='SELL',)
    return render(request, 'your_proposal_seller.html', {'proposals': your_proposals_seller})

def your_proposals_buyer(request):
    your_proposals_buyer = Proposal.objects.filter(user=request.user, type='BUY', )
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
                message=f"Your proposal was accepted by {seller.username}.",
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
                message=f"You accepted the proposal from {buyer.username}.",
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
                message=f"Your proposal was rejected by {seller.username}.",
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
                message=f"Your proposal was accepted by {buyer.username}.",
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
                message=f"You accepted the proposal from {seller.username}.",
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
                message=f"Your proposal was rejected by {buyer.username}.",
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
    trades = Trade.objects.filter(buyer=request.user).select_related('seller', 'buyer', 'proposal').order_by('-created_at')

    # Get search and date filter parameters
    search_query = request.GET.get('search', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Apply search filter
    if search_query:
        trades = trades.filter(
            Q(proposal__description__icontains=search_query) |
            Q(seller__username__icontains=search_query) |
            Q(buyer__username__icontains=search_query) |
            Q(id__icontains=search_query)
        )

    # Apply date range filter
    if start_date:
        trades = trades.filter(created_at__date__gte=start_date)
    if end_date:
        trades = trades.filter(created_at__date__lte=end_date)

    # Add display label
    for trade in trades:
        if trade.proposal.type == 'BUY':
            trade.display_type = f"Accepted & Sold by {trade.seller.username}"
        elif trade.proposal.type == 'SELL':
            trade.display_type = f"Accepted & Bought by {trade.buyer.username}"
        else:
            trade.display_type = trade.proposal.type

    context = {
        'trades': trades,
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'buyer_transaction.html', context)

def seller_transactions_view(request):
    search_query = request.GET.get('search', '').strip()
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

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

    # AJAX request (optional partial rendering)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'partials/transaction_table.html', {'trades': trades})

    return render(request, 'seller_transaction.html', {
        'trades': trades,
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
    })

def admin_transactions_view(request):
    trades = Trade.objects.select_related('buyer', 'seller', 'proposal').annotate(
        display_type=Case(
            When(proposal__type='BUY', then=Value('BUY - Accepted & Sold by Seller')),
            When(proposal__type='SELL', then=Value('SELL - Accepted & Bought by Buyer')),
            default=Value('Unknown'),
            output_field=CharField(),
        )
    ).order_by('-created_at')

    context = {'trades': trades}
    return render(request, 'admin_transactions.html', context)





def dashboard_view(request):
    # 1. Trades count per day (last 10 days)
    trades_per_day_qs = (
        Trade.objects
        .annotate(day=TruncDay('created_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('-day')[:10]
    )
    trades_per_day_qs = reversed(list(trades_per_day_qs))

    trades_labels = [item['day'].strftime('%Y-%m-%d') for item in trades_per_day_qs]
    trades_data = [item['count'] for item in trades_per_day_qs]

    # 2. Total users count
    total_users = User.objects.count()

    # 3. Total energy consumed
    total_energy_consumed = Proposal.objects.aggregate(total=Sum('energy_ask'))['total'] or 0

    # 4. Total energy saved
    total_energy_saved = User.objects.aggregate(total=Sum('total_energy_saved'))['total'] or 0

    # 5. Earnings
    earning = Proposal.objects.aggregate(total=Sum('amount'))['total'] or 0

    # ✅ 6. Recent trades with user info and amount
    recent_trades = (
        Trade.objects
        .select_related('seller')  # Adjust if using `buyer` instead
        .order_by('-created_at')[:5]
    )

    context = {
        'trades_labels': json.dumps(trades_labels),
        'trades_data': json.dumps(trades_data),
        'total_users': total_users,
        'total_energy_consumed': total_energy_consumed,
        'total_energy_saved': total_energy_saved,
        'earning': earning,
        'recent_trades': recent_trades,
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