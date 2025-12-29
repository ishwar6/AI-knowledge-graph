from django.db import connection
from django.views import View


class BusinessUserView(View):
    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM business_user")
        return None
