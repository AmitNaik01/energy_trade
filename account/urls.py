from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import LogoutOnGetView
from django.contrib.auth import views as auth_views
from django.urls import path, include


urlpatterns = [
    # path('', views.index, name= 'index'),
    path('', views.login_view, name='login_view'),
    path('logout/', LogoutOnGetView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('adminpage/', views.dashboard_view, name='adminpage'),
    path('profile/', views.admin_profile_details, name='admin_profile'),
    # path('buyer/', views.buyer, name='buyer'),
    path('buyer/', views.buyer_dashboard, name='buyer'),
    path('profile/buyer', views.buyer_profile_details, name='buyer_profile'),
    path('profile/seller', views.seller_profile_details, name='seller_profile'),
    path('seller_dashboard/', views.seller_dashboard, name='seller'),
    path('users/', views.user_list, name='user_list'),
    path('user/<int:user_id>/', views.user_details, name='user_details'),
    path('user/<int:user_id>/edit/', views.edit_user_details, name='edit_user_details'),
    # path('transactions/', views.transaction_page, name='transactions'),
    path('energyanalytic/', views.energyanalytic_page, name='energyanalytic'),
    path('notification/', views.notification_page, name='notification'),
    path('report/', views.report_page, name='report'),
    path('systemsetting/', views.systemsetting_page, name='systemsetting'),
    path('user/delete/<int:user_id>/', views.delete_user, name='delete_user'),

    path('seller/notifications/', views.seller_notifications_view, name='seller_notifications'),
    path('buyer/notifications/', views.buyer_notifications_view, name='buyer_notifications'),

    path('seller/buyers/', views.seller_buyers_view, name='seller_buyers'),
    path('buyer/sellers/', views.buyer_seller_list_view, name='buyer_seller_list'),



    path('seller/seller-proposals/', views.buyer_proposals_for_seller, name='buyer_proposals_for_seller'),
    path('buyer/buyer-proposals/', views.seller_proposals_for_buyer, name='seller_proposals_for_buyer'),

    path('buyer/create-proposal/', views.create_buyer_proposal, name='create_buyer_proposal'),
    path('create-seller-proposal/', views.create_seller_proposal, name='create_seller_proposal'),

    path('your-proposals-seller/', views.your_proposals_seller, name='your_proposals_seller'),
    path('your-proposals-buyer/', views.your_proposals_buyer, name='your_proposals_buyer'),

    path('seller/process-trade/', views.seller_process_trade, name='seller_process_trade'),
    path('buyer/process-trade/', views.buyer_process_trade, name='buyer_process_trade'),

    path('buyer/transactions/', views.buyer_transactions_view, name='buyer_transactions'),
    path('seller/transactions/', views.seller_transactions_view, name='seller_transactions'),
    path('transactions/', views.admin_transactions_view, name='admin_transactions'),

    # path('forgot-password/', views.forgot_password, name='forgot_password'),
    # path('verify-code/', views.verify_code, name='verify_code'),
    # path('reset-password/', views.reset_password, name='reset_password'),

    # path('forgot-password/', views.forgot_password),
    # path('verify-code/', views.verify_reset_code),
    # path('reset-password/', views.reset_password),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('verify-code/', views.verify_code_view, name='verify_code'),
    path('reset-password/', views.reset_password_view, name='reset_password'),

    path('seller/proposal/edit/<int:proposal_id>/', views.edit_seller_proposal, name='edit_seller_proposal'),
    path('seller/proposal/delete/<int:proposal_id>/', views.delete_seller_proposal, name='delete_seller_proposal'),
    path('download-invoice/<str:trade_id>/', views.download_invoice, name='download_invoice'),
    path('export-trades-csv/', views.export_trades_csv, name='export_trades_csv'),
    path('buyer/proposal/edit/<int:proposal_id>/', views.edit_buyer_proposal, name='edit_buyer_proposal'),
    path('buyer/proposal/delete/<int:proposal_id>/', views.delete_buyer_proposal, name='delete_buyer_proposal'),

    path('captcha/', include('captcha.urls')),





    path('trader_dashboard/', views.trader_dashboard, name='trader'),
    path('trader/sell-energy/', views.trader_sell_energy, name='trader_sell_energy'),
    path('trader/buy-energy/', views.trader_buy_energy, name='trader_buy_energy'),
    path('trader/transactions/', views.trader_transactions_view, name='trader_transactions'),
    path('trader/notifications/', views.trader_notifications_view, name='trader_notifications'),
    path('trader/create-buy-proposal/', views.create_trader_buy_proposal, name='create_trader_buy_proposal'),
    path('trader/your-proposals/', views.your_proposal_buy_trade, name='your_proposal_buy_trade'),
    path('trader/sell/create/', views.create_trader_sell_proposal, name='create_trader_sell_proposal'),
    path('trader/your-sell-proposals/', views.your_proposal_trader_sell, name='your_proposal_trader_sell'),
    path('trader/proposal/edit/<int:proposal_id>/', views.edit_trader_sell_proposal, name='edit_trader_sell_proposal'),
    path('trader/proposal/delete/<int:proposal_id>/', views.delete_trader_sell_proposal, name='delete_trader_sell_proposal'),
    path('trader/proposal/buy/edit/<int:proposal_id>/', views.edit_trader_buy_proposal, name='edit_trader_buy_proposal'),
    path('trader/proposal/buy/delete/<int:proposal_id>/', views.delete_trader_buy_proposal, name='delete_trader_buy_proposal'),
    path('profile/trader', views.trader_profile_details, name='trader_profile'),





    






]

handler404 = 'accounts.views.custom_404_view'
