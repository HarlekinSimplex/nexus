from django.contrib import admin

# Register your models here.
# Register your models here.
from .models import DistributionTargets, BridgeTargets

admin.site.register(DistributionTargets)
admin.site.register(BridgeTargets)
