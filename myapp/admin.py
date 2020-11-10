from django.contrib import admin
from .models import User,Book,Contact,WishList,Cart,Transaction
# Register your models here.
admin.site.register(User)
admin.site.register(Book)
admin.site.register(Contact)
admin.site.register(WishList)
admin.site.register(Cart)
admin.site.register(Transaction)