from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid
from decimal import Decimal
ROLE_CHOICES = [
    ('Admin', 'Admin'),
    ('Seller', 'Seller'),
    ('Buyer', 'Buyer'),
    ('Trader', 'Trader')
]
STATUS_CHOICES = (
    ('active', 'Active'),
    ('inactive', 'Inactive'),
)

class User(AbstractUser):
    is_admin = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)
    is_employee = models.BooleanField(default=False)
    is_trader = models.BooleanField(default=False)


    address = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Buyer')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    address = models.CharField(max_length=255, blank=True, null=True)  # Add this line
    contact_no = models.CharField(max_length=15, blank=True, null=True)
    total_energy_consumed = models.FloatField(default=100.0)  # ✅ Add this
    total_energy_saved = models.FloatField(default=1000.0)
    reset_code = models.CharField(max_length=6, blank=True, null=True)


class Proposal(models.Model):
    PROPOSAL_TYPE_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=PROPOSAL_TYPE_CHOICES)
    description = models.TextField()
    energy_ask = models.PositiveIntegerField(help_text="Amount of energy in kWh")
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in INR")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

def generate_transaction_id():
    return f"TXN-{uuid.uuid4().hex[:10].upper()}"


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('SELL', 'Sell'),
        ('BUY', 'Buy'),
    ]

    id = models.CharField(
        primary_key=True,
        max_length=100,
        editable=False,
        unique=True
    )
    transaction_type = models.CharField(max_length=50)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    proposal = models.ForeignKey('Proposal', on_delete=models.CASCADE)
    user = models.ForeignKey('User', on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # Generate a random UUID if not already set
        if not self.id:
            self.id = f"TXN{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

class Trade(models.Model):
    id = models.CharField(
        primary_key=True,
        max_length=100,
        unique=True,
        editable=False
    )
    status = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trades_as_buyer')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trades_as_seller')
    proposal = models.ForeignKey('Proposal', on_delete=models.CASCADE)


    class Meta:
        db_table = 'account_trade'




    def save(self, *args, **kwargs):
        # Generate alphanumeric ID if it's not set
        if not self.id:
            self.id = f"TRD{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=100)  # e.g. 'trade_created', 'trade_accepted', etc.
    message = models.TextField()
    data = models.JSONField(blank=True, null=True)  # additional trade info or metadata
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.data:
            self.data = self._convert_decimals(self.data)
        super().save(*args, **kwargs)

    def _convert_decimals(self, obj):
        """
        Recursively convert Decimal objects to float in data dict.
        """
        if isinstance(obj, dict):
            return {k: self._convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimals(i) for i in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return obj



def __str__(self):
        return self.get_full_name() or self.username
