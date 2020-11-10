from django.shortcuts import render,redirect
from .models import User,Book,Contact,WishList,Cart,Transaction
from django.core.mail import send_mail
import random
from django.conf import settings
from .paytm import generate_checksum, verify_checksum
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
# Create your views here.



def initiate_payment(request):
    try:
        
        amount = int(request.POST['amount'])
        user = User.objects.get(email=request.session['email'])
        
    except:
        return render(request, 'mycart.html', context={'error': 'Wrong Accound Details or amount'})

    transaction = Transaction.objects.create(made_by=user, amount=amount)
    transaction.save()
    merchant_key = settings.PAYTM_SECRET_KEY

    params = (
        ('MID', settings.PAYTM_MERCHANT_ID),
        ('ORDER_ID', str(transaction.order_id)),
        ('CUST_ID', str(user.email)),
        ('TXN_AMOUNT', str(transaction.amount)),
        ('CHANNEL_ID', settings.PAYTM_CHANNEL_ID),
        ('WEBSITE', settings.PAYTM_WEBSITE),
        # ('EMAIL', request.user.email),
        # ('MOBILE_N0', '9911223388'),
        ('INDUSTRY_TYPE_ID', settings.PAYTM_INDUSTRY_TYPE_ID),
        ('CALLBACK_URL', 'http://localhost:8000/callback/'),
        # ('PAYMENT_MODE_ONLY', 'NO'),
    )

    paytm_params = dict(params)
    checksum = generate_checksum(paytm_params, merchant_key)

    transaction.checksum = checksum
    transaction.save()

    paytm_params['CHECKSUMHASH'] = checksum
    print('SENT: ', checksum)
    return render(request, 'redirect.html', context=paytm_params)

@csrf_exempt
def callback(request):
    if request.method == 'POST':
        received_data = dict(request.POST)
        paytm_params = {}
        paytm_checksum = received_data['CHECKSUMHASH'][0]
        for key, value in received_data.items():
            if key == 'CHECKSUMHASH':
                paytm_checksum = value[0]
            else:
                paytm_params[key] = str(value[0])
        # Verify checksum
        is_valid_checksum = verify_checksum(paytm_params, settings.PAYTM_SECRET_KEY, str(paytm_checksum))
        if is_valid_checksum:
            received_data['message'] = "Checksum Matched"
        else:
            received_data['message'] = "Checksum Mismatched"
            return render(request, 'callback.html', context=received_data)
        return render(request, 'callback.html', context=received_data)



def index(request):
	return render(request,'index.html')

def contact(request):

	if request.method=="POST":
		
		name=request.POST['name']
		email=request.POST['email']
		mobile=request.POST['mobile']
		feedback=request.POST['feedback']

		Contact.objects.create(name=name,email=email,mobile=mobile,feedback=feedback)
		msg="Contact Saved Successfully"
		contacts=Contact.objects.all().order_by('-id')[:10]
		return render(request,'contact.html',{'msg':msg,'contacts':contacts})
	else:
		contacts=Contact.objects.all().order_by('-id')[:10]
		return render(request,'contact.html',{'contacts':contacts})

def signup(request):
	if request.method=="POST":
		f=request.POST['fname']
		l=request.POST['lname']
		e=request.POST['email']
		m=request.POST['mobile']
		p=request.POST['password']
		cp=request.POST['cpassword']
		ut=request.POST['usertype']
		ui=request.FILES['user_image']

		try:

			user=User.objects.get(email=e)
			if user:
				msg="Email Already Registered With Us"
				return render(request,'signup.html',{'msg':msg,'f':f,'l':l})

		except:

			if p==cp:
				User.objects.create(fname=f,lname=l,email=e,mobile=m,password=p,cpassword=cp,usertype=ut,user_image=ui)
				rec=[e,]
				subject="OTP For Successfull Registration"
				otp=random.randint(1000,9999)
				message="Your OTP For Registration Is "+str(otp)
				email_from = settings.EMAIL_HOST_USER
				send_mail(subject, message, email_from, rec)
				return render(request,'otp.html',{'email':e,'otp':otp})
			else:
				msg="Password & Confirm Password Does Not Matched"
				return render(request,'signup.html',{'msg':msg})
	else:
		return render(request,'signup.html')

def login(request):
	if request.method=="POST":

		email=request.POST['email']
		password=request.POST['password']
		usertype=request.POST['usertype']

		try:
			user=User.objects.get(email=email,password=password)
			if usertype=="user":
				try:
					user=User.objects.get(email=email,password=password,usertype=usertype)
					request.session['fname']=user.fname
					request.session['email']=user.email
					wishlists=WishList.objects.filter(user=user)
					request.session['total_wishlist']=len(wishlists)
					carts=Cart.objects.filter(user=user)
					request.session['total_cart']=len(carts)
					request.session['user_image']=user.user_image.url
					return render(request,'index.html')

				except:
					msg="Please Select Proper User Type"
					return render(request,'login.html',{'msg':msg})		
			elif user.usertype=="seller":
				print("Seller")
				request.session['fname']=user.fname
				request.session['email']=user.email
				request.session['user_image']=user.user_image.url
				return render(request,'seller_index.html')
		except Exception as e:
			print(e)
			msg="Email Or Password Is Incorrect"
			return render(request,'login.html',{'msg':msg})
	else:
		return render(request,'login.html')

def validate_otp(request):

	myvar=""
	email=request.POST['email']
	otp=request.POST['otp']
	uotp=request.POST['uotp']
	try:
		myvar=request.POST['myvar']
	except:
		pass

	if otp==uotp and myvar=="forgot_password":
		return render(request,'enter_new_password.html',{'email':email})
	elif otp==uotp:
		try:
			user=User.objects.get(email=email)
			user.status="active"
			user.save()
			return render(request,'login.html')
		except:
			pass
	else:
		msg="Entered OTP Is Not Valid"
		return render(request,'otp.html',{'email':email,'otp':otp,'msg':msg})

def logout(request):

	try:
		del request.session['fname']
		del request.session['email']
		del request.session['total_cart']
		del request.session['total_wishlist']
		del request.session['user_image']
		return render(request,'login.html')
	except:
		return render(request,'login.html')

def forgot_password(request):
	if request.method=="POST":
		email=request.POST['email']
		try:
			user=User.objects.get(email=email)
			rec=[email,]
			subject="OTP For Forgot Password"
			otp=random.randint(1000,9999)
			message="Your OTP For Forgot Password Is "+str(otp)
			email_from = settings.EMAIL_HOST_USER
			send_mail(subject, message, email_from, rec)
			myvar="forgot_password"
			return render(request,'otp.html',{'email':email,'otp':otp,'myvar':myvar})

		except:
			msg="Email Id Does Not Exists"
			return render(request,'enter_email.html',{'msg':msg})	
	else:
		return render(request,'enter_email.html')
def update_password(request):
	email=request.POST['email']
	npassword=request.POST['npassword']
	cnpassword=request.POST['cnpassword']

	if npassword==cnpassword:
		user=User.objects.get(email=email)
		user.password=npassword
		user.cpassword=cnpassword
		user.save()
		return render(request,'login.html')
	else:
		msg="New Password & Confirm New Password Does Not Matched"
		return render(request,'enter_new_password.html',{'email':email,'msg':msg})

def change_password(request):
	if request.method=="POST":

		old_password=request.POST['old_password']
		new_password=request.POST['new_password']
		cnew_password=request.POST['cnew_password']

		user=User.objects.get(email=request.session['email'])
		if old_password=="" or new_password=="" or cnew_password=="":
			msg="All Fields Are Mandatory"
			return render(request,'change_password.html',{'msg':msg})
		if user.password==old_password:
			if new_password==cnew_password:
				user.password=new_password
				user.cpassword=new_password
				user.save()
				return redirect('logout')
			else:
				msg="New Password & Confrim New Password Does Not Matched"
				return render(request,'change_password.html',{'msg':msg})
		else:
			msg="Old Password Does Not	Matched"
			return render(request,'change_password.html',{'msg':msg})

	else:
		return render(request,'change_password.html')

def add_book(request):
	if request.method=="POST":
		user=User.objects.get(email=request.session['email'])
		bc=request.POST['book_category']
		bn=request.POST['book_name']
		ba=request.POST['book_author']
		bp=request.POST['book_price']
		bq=request.POST['book_qty']
		bd=request.POST['book_desc']
		bi=request.FILES['book_image']

		books=Book.objects.filter(user=user)
		for b in books:
			if b.book_name.lower()==bn.lower():
				msg="Book Is Allready In Your List"
				return render(request,'add_book.html',{'msg':msg})
		else:
			Book.objects.create(book_category=bc,book_name=bn,book_author=ba,book_price=bp,book_qty=bq,book_desc=bd,book_image=bi,user=user)
			msg="Book Added Successfully"
			return render(request,'add_book.html',{'msg':msg})
	else:
		return render(request,'add_book.html')

def view_book(request):
	user=User.objects.get(email=request.session['email'])
	books=Book.objects.filter(user=user)
	return render(request,'view_book.html',{'books':books})

def seller_index(request):
	return render(request,'seller_index.html')

def book_detail(request,pk):
	book=Book.objects.get(pk=pk)
	return render(request,'book_detail.html',{'book':book})

def stock_avaibility(request,pk):
	book=Book.objects.get(pk=pk)
	if book.book_stock=="Available":
		book.book_stock="Unavailable"
		book.save()
	else:
		book.book_stock="Available"
		book.save()
	return redirect('book_detail',pk)

def book_delete(request,pk):
	book=Book.objects.get(pk=pk)
	book.delete()
	return redirect('view_book')

def edit_book(request,pk):
	if request.method=="POST":
		book=Book.objects.get(pk=pk)
		book.book_name=request.POST['book_name']
		book.book_author=request.POST['book_author']
		book.book_price=request.POST['book_price']
		book.book_desc=request.POST['book_desc']
		book.book_qty=request.POST['book_qty']
		try:
			if request.FILES['book_image']:
				book.book_image=request.FILES['book_image']
				book.save()
				return redirect('view_book')
		except:
			book.save()
			return redirect('view_book')
	else:
		book=Book.objects.get(pk=pk)
		return render(request,'edit_book.html',{'book':book})

def unavailable_books(request):
	user=User.objects.get(email=request.session['email'])
	books=Book.objects.filter(book_stock="Unavailable",user=user)
	print(books)
	return render(request,'unavailable_books.html',{'books':books})

def search_book(request):
	user=User.objects.get(email=request.session['email'])
	search=request.POST['search']
	books=Book.objects.filter(book_name__contains=search,user=user)
	return render(request,'search_book.html',{'books':books})

def show_book(request,bn):
	books=Book.objects.filter(book_name__contains=bn)
	return render(request,'show_book.html',{'books':books})

def user_book_detail(request,pk):

	flag=False
	flag1=False
	book=Book.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	wishlists=WishList.objects.filter(user=user,book=book)
	carts=Cart.objects.filter(user=user,book=book)
	for i in wishlists:
		if i.book.pk==book.pk:
			flag=True
			break
	for i in carts:
		if i.book.pk==book.pk:
			flag1=True
			break
	return render(request,'user_book_detail.html',{'book':book,'flag':flag,'flag1':flag1})

def add_to_wishlist(request,pk):
	
	book=Book.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	WishList.objects.create(user=user,book=book)
	return redirect('mywishlist')	

def remove_from_wishlist(request,pk):
	
	book=Book.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	wishlist=WishList.objects.get(user=user,book=book)
	wishlist.delete()
	return redirect('mywishlist')

def mywishlist(request):
	user=User.objects.get(email=request.session['email'])
	wishlists=WishList.objects.filter(user=user)
	request.session['total_wishlist']=len(wishlists)
	return render(request,'mywishlist.html',{'wishlists':wishlists})

def add_to_cart(request,pk):
	
	book=Book.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	Cart.objects.create(user=user,book=book,total_price=book.book_price,total_qty=1)
	return redirect('mycart')	

def remove_from_cart(request,pk):
	
	book=Book.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	cart=Cart.objects.get(user=user,book=book)
	cart.delete()
	return redirect('mycart')

def mycart(request):
	net_price=0
	user=User.objects.get(email=request.session['email'])
	carts=Cart.objects.filter(user=user)
	for i in carts:
		net_price=net_price+i.total_price
	request.session['total_cart']=len(carts)
	return render(request,'mycart.html',{'carts':carts,'net_price':net_price})

def move_to_cart(request,pk):

	book=Book.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	Cart.objects.create(user=user,book=book)
	wishlist=WishList.objects.get(user=user,book=book)
	wishlist.delete()
	wishlists=WishList.objects.filter(user=user)
	request.session['total_wishlist']=len(wishlists)
	return redirect('mycart')

def profile(request):
	if request.method=="POST":
		user=User.objects.get(email=request.session['email'])
		user.fname=request.POST['fname']
		user.lname=request.POST['lname']
		user.email=request.POST['email']
		user.mobile=request.POST['mobile']
		try:
			if request.FILES['user_image']:
				user.user_image=request.FILES['user_image']
				user.save()
				request.session['user_image']=user.user_image.url
				return redirect('index')
		except:
			user.save()
			return redirect('index')
	else:
		user=User.objects.get(email=request.session['email'])
		return render(request,'profile.html',{'user':user})

def update_price(request):
	price=request.POST['price']
	qty=request.POST['qty']
	pk=request.POST['pk']

	cart=Cart.objects.get(pk=pk)
	total_price=int(price)*int(qty)
	cart.total_price=total_price
	cart.total_qty=qty
	cart.save()
	return redirect("mycart")

@csrf_exempt
def validate_username(request):
	username = request.POST['username']
	data = {'is_taken': User.objects.filter(email__iexact=username).exists()}
	return JsonResponse(data)