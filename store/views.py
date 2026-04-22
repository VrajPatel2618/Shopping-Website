from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from .models import Product, Category, Order, OrderItem


# -------------------------------------------------------
# Public Pages
# -------------------------------------------------------

def home(request):
    products = Product.objects.filter(is_active=True).order_by('-id')[:4]
    return render(request, "store/home.html", {"products": products})

def earbuds(request):
    products = Product.objects.filter(category__name__icontains="earbud", is_active=True)
    return render(request, "store/earbuds.html", {"products": products})

def headphones(request):
    products = Product.objects.filter(category__name__icontains="headphone", is_active=True)
    return render(request, "store/headphones.html", {"products": products})

def watches(request):
    products = Product.objects.filter(category__name__icontains="watch", is_active=True)
    return render(request, "store/watches.html", {"products": products})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    related = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(id=product_id)[:4]
    return render(request, "store/product_detail.html", {
        "product": product,
        "related": related,
    })

def search(request):
    q = request.GET.get('q', '').strip()
    results = Product.objects.filter(
        Q(name__icontains=q) | Q(description__icontains=q),
        is_active=True
    ) if q else Product.objects.none()

    # Build recommendations: same-category products not already in results
    recommendations = Product.objects.none()
    if results.exists():
        cat_ids = results.values_list('category_id', flat=True).distinct()
        result_ids = results.values_list('id', flat=True)
        recommendations = Product.objects.filter(
            category_id__in=cat_ids, is_active=True
        ).exclude(id__in=result_ids).order_by('?')[:6]
        
        if not recommendations.exists():
            recommendations = Product.objects.filter(is_active=True).exclude(id__in=result_ids).order_by('-id')[:6]
    elif not q:
        # No query → show some popular/featured items
        recommendations = Product.objects.filter(is_active=True).order_by('-id')[:6]

    return render(request, "store/search_results.html", {
        "results": results,
        "query": q,
        "recommendations": recommendations,
    })


def search_suggest(request):
    """AJAX endpoint: returns up to 6 product suggestions with image and category."""
    q = request.GET.get('q', '').strip()
    data = []
    if q:
        products = Product.objects.filter(
            name__icontains=q, is_active=True
        ).select_related('category')[:6]
        for p in products:
            image_url = ''
            if p.image:
                image_url = p.image.url
            elif p.image_url:
                image_url = p.image_url
            data.append({
                'id': p.id,
                'name': p.name,
                'price': str(p.price),
                'image': image_url,
                'category': p.category.name if p.category else '',
            })
    return JsonResponse({'results': data})


# -------------------------------------------------------
# Cart
# -------------------------------------------------------

@login_required(login_url='login')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    order, created = Order.objects.get_or_create(user=request.user, is_completed=False)
    order_item, item_created = OrderItem.objects.get_or_create(order=order, product=product)

    if not item_created:
        order_item.quantity += 1

    order_item.price_at_purchase = product.price
    order_item.save()

    order.total_price = sum(item.product.price * item.quantity for item in order.items.all())
    order.save()

    messages.success(request, f"{product.name} added to your cart.")
    return redirect('cart')

@login_required(login_url='login')
def increase_quantity(request, item_id):
    item = get_object_or_404(
        OrderItem, id=item_id, order__user=request.user, order__is_completed=False
    )
    item.quantity += 1
    item.save()
    order = item.order
    order.total_price = sum(i.product.price * i.quantity for i in order.items.all())
    order.save()
    return redirect('cart')

@login_required(login_url='login')
def decrease_quantity(request, item_id):
    item = get_object_or_404(
        OrderItem, id=item_id, order__user=request.user, order__is_completed=False
    )
    order = item.order
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()
    order.total_price = sum(i.product.price * i.quantity for i in order.items.all())
    order.save()
    return redirect('cart')

@login_required(login_url='login')
def remove_from_cart(request, item_id):
    item = get_object_or_404(
        OrderItem, id=item_id, order__user=request.user, order__is_completed=False
    )
    order = item.order
    product_name = item.product.name
    item.delete()
    order.total_price = sum(i.product.price * i.quantity for i in order.items.all())
    order.save()
    messages.success(request, f"{product_name} removed from cart.")
    return redirect('cart')

@login_required(login_url='login')
def cart(request):
    # Admin has no cart — redirect to Orders Panel
    if request.user.is_superuser:
        return redirect('admin_orders')
    order = Order.objects.filter(user=request.user, is_completed=False).first()
    past_orders = Order.objects.filter(user=request.user, is_completed=True).order_by('-created_at')
    return render(request, "store/cart.html", {"order": order, "past_orders": past_orders})

@login_required(login_url='login')
def checkout(request):
    order = Order.objects.filter(user=request.user, is_completed=False).first()
    if order and order.items.exists():
        for item in order.items.all():
            if item.product.stock < item.quantity:
                messages.error(request, f"Not enough stock for {item.product.name}.")
                return redirect('cart')

        for item in order.items.all():
            product = item.product
            product.stock -= item.quantity
            product.save()

        order.is_completed = True
        order.status = Order.STATUS_PENDING
        order.save()
        messages.success(request, "Your order has been placed successfully!")
    else:
        messages.warning(request, "Your cart is empty.")
    return redirect('cart')


# -------------------------------------------------------
# Admin / POS
# -------------------------------------------------------

@login_required(login_url='login')
def pos_view(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('home')

    if request.method == "POST":
        product_id = request.POST.get("product_id")
        quantity = int(request.POST.get("quantity", 1))
        product = get_object_or_404(Product, id=product_id)

        if product.stock >= quantity:
            order = Order.objects.create(
                user=request.user, is_completed=True, payment_method="Cash"
            )
            OrderItem.objects.create(
                order=order, product=product, quantity=quantity,
                price_at_purchase=product.price
            )
            order.total_price = product.price * quantity
            order.save()
            product.stock -= quantity
            product.save()
            messages.success(request, f"Sale of {quantity}x {product.name} completed!")
        else:
            messages.error(request, f"Insufficient stock for {product.name}.")
        return redirect('pos')

    products = Product.objects.filter(is_active=True).order_by('name')
    return render(request, "store/pos.html", {"products": products})

@login_required(login_url='login')
def generate_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if not request.user.is_superuser and order.user != request.user:
        messages.error(request, "Access denied.")
        return redirect('home')
    return render(request, "store/invoice.html", {"order": order})

@login_required(login_url='login')
def user_panel(request):
    if request.method == "POST" and request.user.is_superuser:
        action = request.POST.get("action")
        try:
            if action == "add_product":
                category = Category.objects.get(id=request.POST.get("category"))
                product = Product.objects.create(
                    category=category,
                    name=request.POST.get("name"),
                    description=request.POST.get("description"),
                    price=request.POST.get("price"),
                    image_url=request.POST.get("image_url"),
                    stock=request.POST.get("stock", 0)
                )
                if request.FILES.get('image'):
                    product.image = request.FILES['image']
                    product.save()
                messages.success(request, "Product added successfully!")

            elif action == "edit_product":
                product = get_object_or_404(Product, id=request.POST.get("product_id"))
                product.category = Category.objects.get(id=request.POST.get("category"))
                product.name = request.POST.get("name")
                product.description = request.POST.get("description")
                product.price = request.POST.get("price")
                product.image_url = request.POST.get("image_url")
                product.stock = request.POST.get("stock", 0)
                if request.FILES.get('image'):
                    product.image = request.FILES['image']
                product.save()
                messages.success(request, "Product updated successfully!")

            elif action == "delete_product":
                product = get_object_or_404(Product, id=request.POST.get("product_id"))
                product.delete()
                messages.success(request, "Product deleted successfully!")

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
        return redirect('user_panel')

    context = {}
    if request.user.is_superuser:
        context["all_products"] = Product.objects.all().order_by('-id')
        context["categories"] = Category.objects.all()
    return render(request, "store/user_panel.html", context)


# -------------------------------------------------------
# Auth
# -------------------------------------------------------

def login_user(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect("home")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    form = AuthenticationForm()
    return render(request, "store/login.html", {"form": form})

def register_user(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Registration successful.")
            return redirect("home")
        messages.error(request, "Unsuccessful registration. Invalid information.")
    form = UserCreationForm()
    return render(request, "store/register.html", {"form": form})

def logout_user(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect("home")


@login_required(login_url='login')
def edit_profile(request):
    user = request.user
    # Detect if the user signed in via Google
    is_google_user = user.socialaccount_set.filter(provider='google').exists()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_info":
            new_username = request.POST.get("username", "").strip()
            new_email    = request.POST.get("email", "").strip()

            from django.contrib.auth.models import User as AuthUser
            if new_username and new_username != user.username:
                if AuthUser.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                    messages.error(request, "That username is already taken.")
                    return redirect("edit_profile")
                user.username = new_username

            if new_email:
                user.email = new_email

            user.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("edit_profile")

        elif action == "change_password" and not is_google_user:
            current  = request.POST.get("current_password", "")
            new_pw   = request.POST.get("new_password", "")
            confirm  = request.POST.get("confirm_password", "")

            if not user.check_password(current):
                messages.error(request, "Current password is incorrect.")
                return redirect("edit_profile")
            if len(new_pw) < 8:
                messages.error(request, "New password must be at least 8 characters.")
                return redirect("edit_profile")
            if new_pw != confirm:
                messages.error(request, "New passwords do not match.")
                return redirect("edit_profile")

            user.set_password(new_pw)
            user.save()
            # Keep user logged in after password change
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully!")
            return redirect("edit_profile")

    return render(request, "store/edit_profile.html", {
        "is_google_user": is_google_user,
    })


# -------------------------------------------------------
# Delete Order
# -------------------------------------------------------

@login_required(login_url='login')
def delete_order(request, order_id):
    """Permanently delete a completed order for the logged-in user.
    Because it deletes from the DB, it's also removed from Django admin."""
    order = get_object_or_404(Order, id=order_id, user=request.user, is_completed=True)
    if request.method == 'POST':
        order_num = order.id
        order.delete()  # CASCADE deletes all OrderItems too
        messages.success(request, f"Order #{order_num} has been deleted.")
    return redirect('cart')


# -------------------------------------------------------
# Admin Orders Panel
# -------------------------------------------------------

@login_required(login_url='login')
def admin_orders(request):
    """Admin-only: list all customer orders."""
    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('home')
    orders = Order.objects.filter(is_completed=True).select_related('user').order_by('-created_at')
    return render(request, 'store/admin_orders.html', {'orders': orders})


@login_required(login_url='login')
def admin_order_detail(request, order_id):
    """Admin-only: view full details of a single order."""
    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('home')
    order = get_object_or_404(Order, id=order_id, is_completed=True)
    # Try to get profile (phone/address) if a UserProfile model exists
    return render(request, 'store/admin_order_detail.html', {'order': order})


@login_required(login_url='login')
def admin_accept_order(request, order_id):
    """Admin-only: mark order as Accepted."""
    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('home')
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, is_completed=True)
        if order.status == Order.STATUS_PENDING:
            order.status = Order.STATUS_ACCEPTED
            order.save()
            messages.success(request, f"Order #{order.id} has been accepted.")
        else:
            messages.warning(request, f"Order #{order.id} cannot be accepted at this stage.")
    return redirect('admin_order_detail', order_id=order_id)


@login_required(login_url='login')
def admin_deliver_order(request, order_id):
    """Admin-only: mark order as Delivered → auto Completed."""
    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('home')
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, is_completed=True)
        if order.status == Order.STATUS_ACCEPTED:
            order.status = Order.STATUS_COMPLETED
            order.save()
            messages.success(request, f"Order #{order.id} has been delivered and marked as Completed.")
        else:
            messages.warning(request, f"Order #{order.id} must be accepted before marking as delivered.")
    return redirect('admin_order_detail', order_id=order_id)
