from django.contrib import admin

# Register your models here.
from .models import DistributionTarget, BridgeTarget

admin.site.register(DistributionTarget)
admin.site.register(BridgeTarget)
