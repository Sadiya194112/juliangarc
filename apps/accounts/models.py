from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, full_name, email, phone, password=None, **extra_fields):
        if not full_name:
            raise ValueError("The full name must be set.")
        if not email:
            raise ValueError("The email must be set.")
        if not phone:
            raise ValueError("The phone must be set.")

        email = self.normalize_email(email)
        user = self.model(full_name=full_name, email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, full_name, email, phone, password=None, **extra_fields):
        extra_fields.setdefault("role", User.USER_TYPES[2][0])
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        if not password:
            raise ValueError("Superuser must have a password.")

        return self.create_user(full_name, email, phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPES = (
        ("user", "User"),
        ("host", "Host"),
        ("admin", "Admin"),
    )

    role = models.CharField(max_length=10, choices=USER_TYPES, default="user")
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=15,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,15}$",
                message="Phone number must be in the format: '+123...'. Up to 15 digits allowed.",
            )
        ],
    )
    picture = models.ImageField(upload_to="profile_pics/", blank=True, null=True)
    terms_privacy = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)

    otp = models.CharField(max_length=6, null=True, blank=True, editable=False)
    otp_expiry = models.DateTimeField(null=True, blank=True, editable=False)
    is_verified = models.BooleanField(default=False)

    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_account_id = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "phone"]

    def is_otp_expired(self):
        return not self.otp_expiry or timezone.now() > self.otp_expiry

    def get_full_name(self):
        return self.full_name

    def __str__(self):
        return f"{self.full_name} ({self.role})"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    total_vehicles = models.IntegerField(default=0)
    preferred_charger_types = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.user.full_name
