from django.db import models


class BusinessUser(models.Model):
    name = models.CharField(max_length=255)
    organization = models.ForeignKey("Organization", on_delete=models.CASCADE)


class Organization(models.Model):
    title = models.CharField(max_length=255)
