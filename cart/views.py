from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from store.models import Product, Variation
from .models import Cart, CartItem

# Create your views here.


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        request.session.create()
        cart = request.session.session_key
    return cart


def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    product_variations = []

    if request.method == "POST":
        for item in request.POST:
            key = item
            value = request.POST[key]
            try:
                variation = Variation.objects.get(
                    product=product, variation_category__iexact=key, variation_value__iexact=value)
                product_variations.append(variation)
            except Variation.DoesNotExist:
                print(f"Variation not found: {key} - {value}")

    print(f"Product Variations: {product_variations}")

    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

    is_cart_item_exists = CartItem.objects.filter(
        product=product, cart=cart).exists()

    if is_cart_item_exists:
        cart_item = CartItem.objects.filter(product=product, cart=cart)
        ex_var_list = []
        id_list = []

        for item in cart_item:
            existing_variations = item.variations.all()
            ex_var_list.append(list(existing_variations))
            id_list.append(item.id)

        print(f"Existing Variations List: {ex_var_list}")

        if product_variations in ex_var_list:
            index = ex_var_list.index(product_variations)
            item_id = id_list[index]
            item = CartItem.objects.get(product=product, id=item_id)
            item.quantity += 1
            item.save()
            print("Quantity Increased")
        else:
            item = CartItem.objects.create(
                product=product, quantity=1, cart=cart)
            if len(product_variations) > 0:
                item.variations.clear()
                item.variations.add(*product_variations)
            item.save()
            print("New Cart Item Created")
    else:
        cart_item = CartItem.objects.create(
            product=product, quantity=1, cart=cart)
        if len(product_variations) > 0:
            cart_item.variations.clear()
            cart_item.variations.add(*product_variations)
        cart_item.save()
        print("New Cart Item Created")

    return redirect("cart")


def remove_cart(request, product_id, cart_item_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    try:
        cart_item = CartItem.objects.get(
            product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect("cart")


def remove_cart_item(request, product_id, cart_item_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(
        product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect("cart")


def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity = cart_item.quantity
        tax = (2*total)/100
        grand_total = total+tax

    except Cart.DoesNotExist:
        pass

    context = {
        "total": total,
        "quantity": quantity,
        "cart_items": cart_items,
        "tax": tax,
        "grand_total": grand_total,
    }
    return render(request, 'Pixelcart/cart.html', context)
