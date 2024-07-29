import datetime
from django.core.mail import EmailMessage
import json
from urllib import request
from django.forms import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render

from cart.models import CartItem
from store.models import Product
from orders.models import Order, OrderProduct, Payment
from . forms import OrderForm
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
import logging
# Create your views here.


def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(
        user=request.user, is_ordered=False, order_number=body['orderID'])
    # print(body)
    # store transaction details inside the payments model
    payment = Payment(
        user=request.user,
        payment_id=body['transID'],
        payment_method=body["payment_method"],
        amount_paid=order.order_total,
        status=body['status'],
    )
    payment.save()

    order.is_ordered = True
    order.payment = payment
    order.save()
# move the cart items to order product table

    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product.id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.status = True
        orderproduct.save()

        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()

# Reduce the quantity the sold products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

# clear cart
    CartItem.objects.filter(user=request.user).delete()

# Send oredr received mail to the customers

    mail_subject = "Thank you for your order!"
    message = render_to_string("PixelCart/order_received_email.html", {
        'user': request.user,
        'order': order,
    })

    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()


# Send order number and transaction id back to sendData method via Json Response
    data = {
        "order_number": order.order_number,
        "transaction_id": payment.payment_id,
    }
    return JsonResponse(data)

    return render(request, "PixelCart/payments.html")


@login_required  # Apply login_required decorator to ensure the user is authenticated
def place_order(request, total=0, quantity=0):
    current_user = request.user

    # if the cart count is zero or less than zero, then the user will be redirected to shop/store
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0

    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity  # Increment quantity inside the loop

    # Calculate tax and grand total outside the loop
    tax = (2 * total) / 100
    grand_total = total + tax

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():

            # store all the billing information inside "Order" table
            data = Order()

            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")  # 20210305

            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            # to get the order object
            order = Order.objects.get(
                user=current_user, is_ordered=False, order_number=order_number)
            context = {
                "order": order,
                "cart_items": cart_items,
                "total": total,
                "tax": tax,
                "grand_total": grand_total,
            }

            return render(request, "PixelCart/payments.html", context)
        else:

            return redirect("checkout")


def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')
    try:
        order = Order.objects.get(
            order_number=order_number, is_ordered=True)
        order_products = OrderProduct.objects.filter(order_id=order.id)
        payment = Payment.objects.get(payment_id=transID)
        subtotal = 0
        for i in order_products:
            subtotal += (i.product.price * i.quantity)

        # if float(subtotal) <= float(payment.amount):
        #     order.is_ordered = True
        #     order.payment_id = transID
        #     order.save()
        #     messages.success(request, f'Your order has been placed successfully!')
        #     return redirect('home')
        # else:
        #     messages.warning(request, 'Payment unsuccesful, please check your information and try again or contact us for assistance.
        #     messages.error(request, 'Payment was unsuccesful! Please contact support for assistance.')

        context = {
            "order": order,
            "order_products": order_products,
            "order_number": order.order_number,
            "transId": payment.payment_id,
            'subtotal': subtotal,
            'payment': payment,
        }
        return render(request, "Pixelcart/order_complete.html", context)

    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect("checkout")
