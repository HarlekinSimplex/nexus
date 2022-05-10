import RNS
from django.db import models


# import datetime
# from django.utils import timezone


# Create your models here.
class DistributionTargets(models.Model):
    destination_hash = models.CharField(max_length=22, db_index=True, null=False, unique=True)
    private_key = models.BinaryField()
    public_key = models.BinaryField()
    last_heard = models.TimeField(auto_now=True)
    announced_role = models.JSONField()

    def __str__(self):
        return RNS.prettyhexrep(self.destination_hash)


class BridgeTargets(models.Model):
    url = models.URLField()
    cluster = models.CharField(max_length=32)

    def __str__(self):
        return "<BRIDGE-TO:" + self.cluster + ">"
