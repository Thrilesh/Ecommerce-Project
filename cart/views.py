from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from store.models import Product, Variation
from .models import Cart, CartItem
from django.contrib.auth.decorators import login_required


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        request.session.create()
        cart = request.session.session_key
    return cart


# ... (your other imports)


def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)

    # If user is authenticated
    if current_user.is_authenticated:
        product_variations = []

        if request.method == "POST":
            for item in request.POST:
                key = item
                value = request.POST[key]

                try:
                    variations = Variation.objects.get(
                        product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variations.append(variations)
                except:
                    pass

        cart = Cart.objects.get_or_create(cart_id=_cart_id(request))[0]

        is_cart_item_exists = CartItem.objects.filter(
            product=product, user=current_user, cart=cart).exists()

        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(
                product=product, user=current_user, cart=cart)

            ex_var_lists = []

            for item in cart_item:
                existing_variations = list(item.variations.all())
                ex_var_lists.append(existing_variations)

            if product_variations in ex_var_lists:
                # Increase the cart item quantity
                index = ex_var_lists.index(product_variations)
                item = cart_item[index]
                item.quantity += 1
                item.save()
            else:
                item = CartItem.objects.create(
                    product=product,
                    quantity=1,
                    user=current_user,
                    cart=cart
                )
                if len(product_variations) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variations)
                item.save()
        else:
            item = CartItem.objects.create(
                product=product,
                quantity=1,
                user=current_user,
                cart=cart
            )
            if len(product_variations) > 0:
                item.variations.clear()
                item.variations.add(*product_variations)
            item.save()
        return redirect("cart")

    # If the user is not authenticated
    else:
        product_variations = []

        if request.method == "POST":
            for item in request.POST:
                key = item
                value = request.POST[key]

                try:
                    variations = Variation.objects.get(
                        product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variations.append(variations)
                except:
                    pass

        cart = Cart.objects.get_or_create(cart_id=_cart_id(request))[0]

        is_cart_item_exists = CartItem.objects.filter(
            product=product, cart=cart, user__isnull=True).exists()

        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(
                product=product, cart=cart, user__isnull=True)

            ex_var_lists = []

            for item in cart_item:
                existing_variations = list(item.variations.all())
                ex_var_lists.append(existing_variations)

            if product_variations in ex_var_lists:
                # Increase the cart item quantity
                index = ex_var_lists.index(product_variations)
                item = cart_item[index]
                item.quantity += 1
                item.save()
            else:
                item = CartItem.objects.create(
                    product=product,
                    quantity=1,
                    cart=cart
                )
                if len(product_variations) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variations)
                item.save()

        else:
            item = CartItem.objects.create(
                product=product,
                quantity=1,
                cart=cart,
            )
            if len(product_variations) > 0:
                item.variations.clear()
                item.variations.add(*product_variations)
            item.save()

        return redirect("cart")


def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(
                product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
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
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(
            product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(
            product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect("cart")


def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(
                user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity = cart_item.quantity
        tax = (2 * total) / 100
        grand_total = total + tax

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


@login_required(login_url="login")
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0

        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(
                user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity = cart_item.quantity

        # Calculate tax and grand total outside the loop
        tax = (2 * total) / 100
        grand_total = total + tax

    except Cart.DoesNotExist:
        pass

    context = {
        "total": total,
        "quantity": quantity,
        "cart_items": cart_items,
        "tax": tax,
        "grand_total": grand_total,
    }
    return render(request, "PixelCart/checkout.html", context)
