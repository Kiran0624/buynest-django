from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product
from .models import Cart, CartItem
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from store.models import Variation

# Create your views here.

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    product = Product.objects.get(id=product_id) # Get the product
    product_variation = []
    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]
            
            try:
                variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                product_variation.append(variation) # Append the variation to the list
            except:
                pass
        

    try:
        cart = Cart.objects.get(cart_id=_cart_id(request)) # Get the cart using the cart_id present in the session
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id = _cart_id(request)
        )
    cart.save()
    
    is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists() # Check if the cart item already exists
    if is_cart_item_exists:
        cart_item = CartItem.objects.filter(product=product, cart=cart) # Get the cart item
        ex_var_list = []
        id = []
        for item in cart_item:
            existing_variation = item.variation.all()
            ex_var_list.append(list(existing_variation))
            id.append(item.id)
        
        if product_variation in ex_var_list:
            index = ex_var_list.index(product_variation)
            item = CartItem.objects.get(product=product, id=id[index])
            item.quantity += 1
            item.save()
        else:
            item = CartItem.objects.create(product = product, quantity = 1, cart = cart)
            if len(product_variation) > 0:
                item.variation.clear() # Clear the existing variations
                item.variation.add(*product_variation) # Add the new variations
            item.save()
    else:
        cart_item = CartItem.objects.create(
            product = product,
            quantity = 1,
            cart = cart
        )
        if len(product_variation) > 0:
            cart_item.variation.clear()
            cart_item.variation.add(*product_variation)
        cart_item.save()
    
    return redirect('cart')

def remove_cart(request, product_id, cart_item_id):
    cart = Cart.objects.get(cart_id=_cart_id(request)) # Get the cart using the cart_id present in the session
    product = get_object_or_404(Product, id=product_id) # Get the product
    try:
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id) # Get the cart item
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    
    return redirect('cart')

def remove_cart_item(request, product_id, cart_item_id):
    cart = Cart.objects.get(cart_id=_cart_id(request)) # Get the cart using the cart_id present in the session
    product = get_object_or_404(Product, id=product_id) # Get the product
    cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id) # Get the cart item
    cart_item.delete()
    
    return redirect('cart')

def cart(request, total = 0, quantity = 0, cart_items = None):
    tax = 0
    grand_total = 0
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request)) # Get the cart using the cart_id present in the session
        cart_items = CartItem.objects.filter(cart=cart, is_active=True) # Get all the cart items
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity) # Calculate the total price
            quantity += cart_item.quantity # Calculate the total quantity
        tax = (2 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)