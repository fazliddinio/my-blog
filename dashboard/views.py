from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_POST
from blog.models import (
    Post, Project, Product, ProductBullet,
    NewsletterSubscriber, NewsletterIssue, ContactMessage,
    UsesCategory, UsesItem, TimelineEntry,
)
from .forms import (
    PostForm, ProjectForm, ProductForm, ProductBulletForm,
    NewsletterIssueForm, UsesCategoryForm, UsesItemForm, TimelineEntryForm,
)


# -------- Auth --------

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'),
        )
        if user is not None:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard:index'))
        messages.error(request, 'Invalid username or password.')
    return render(request, 'dashboard/login.html')


def logout_view(request):
    logout(request)
    return redirect('blog:home')


# -------- Dashboard --------

@login_required(login_url='/dashboard/login/')
def index(request):
    stats = {
        'posts': Post.objects.count(),
        'subscribers': NewsletterSubscriber.objects.filter(is_active=True).count(),
        'messages': ContactMessage.objects.filter(is_read=False).count(),
        'projects': Project.objects.count(),
    }
    recent_messages = ContactMessage.objects.all()[:5]
    recent_subscribers = NewsletterSubscriber.objects.all()[:5]
    return render(request, 'dashboard/index.html', {
        'stats': stats,
        'recent_messages': recent_messages,
        'recent_subscribers': recent_subscribers,
    })


# -------- Posts CRUD --------

@login_required(login_url='/dashboard/login/')
def posts(request):
    return render(request, 'dashboard/posts.html', {
        'posts': Post.objects.all(),
    })


@login_required(login_url='/dashboard/login/')
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post created.')
            return redirect('dashboard:posts')
    else:
        form = PostForm()
    return render(request, 'dashboard/post_form.html', {'form': form, 'editing': False})


@login_required(login_url='/dashboard/login/')
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post updated.')
            return redirect('dashboard:posts')
    else:
        form = PostForm(instance=post)
    return render(request, 'dashboard/post_form.html', {'form': form, 'editing': True})


@login_required(login_url='/dashboard/login/')
@require_POST
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.delete()
    messages.success(request, 'Post deleted.')
    return redirect('dashboard:posts')


# -------- Projects CRUD --------

@login_required(login_url='/dashboard/login/')
def projects(request):
    return render(request, 'dashboard/projects.html', {
        'projects': Project.objects.all(),
    })


@login_required(login_url='/dashboard/login/')
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project created.')
            return redirect('dashboard:projects')
    else:
        form = ProjectForm()
    return render(request, 'dashboard/project_form.html', {'form': form, 'editing': False})


@login_required(login_url='/dashboard/login/')
def project_edit(request, pk):
    obj = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated.')
            return redirect('dashboard:projects')
    else:
        form = ProjectForm(instance=obj)
    return render(request, 'dashboard/project_form.html', {'form': form, 'editing': True})


@login_required(login_url='/dashboard/login/')
@require_POST
def project_delete(request, pk):
    get_object_or_404(Project, pk=pk).delete()
    messages.success(request, 'Project deleted.')
    return redirect('dashboard:projects')


# -------- Products CRUD --------

@login_required(login_url='/dashboard/login/')
def products(request):
    return render(request, 'dashboard/products.html', {
        'products': Product.objects.prefetch_related('bullets').all(),
    })


@login_required(login_url='/dashboard/login/')
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            _save_bullets(request, product)
            messages.success(request, 'Product created.')
            return redirect('dashboard:products')
    else:
        form = ProductForm()
    return render(request, 'dashboard/product_form.html', {'form': form, 'editing': False, 'bullets': []})


@login_required(login_url='/dashboard/login/')
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            _save_bullets(request, product)
            messages.success(request, 'Product updated.')
            return redirect('dashboard:products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'dashboard/product_form.html', {
        'form': form, 'editing': True, 'bullets': product.bullets.all(),
    })


def _save_bullets(request, product):
    texts_en = request.POST.getlist('bullet_text_en')
    texts_uz = request.POST.getlist('bullet_text_uz')
    product.bullets.all().delete()
    for i, (en, uz) in enumerate(zip(texts_en, texts_uz)):
        if en.strip():
            ProductBullet.objects.create(product=product, text_en=en.strip(), text_uz=uz.strip(), order=i)


@login_required(login_url='/dashboard/login/')
@require_POST
def product_delete(request, pk):
    get_object_or_404(Product, pk=pk).delete()
    messages.success(request, 'Product deleted.')
    return redirect('dashboard:products')


# -------- Newsletter --------

@login_required(login_url='/dashboard/login/')
def newsletter(request):
    return render(request, 'dashboard/newsletter.html', {
        'issues': NewsletterIssue.objects.all(),
        'subscribers': NewsletterSubscriber.objects.all(),
    })


@login_required(login_url='/dashboard/login/')
def issue_create(request):
    if request.method == 'POST':
        form = NewsletterIssueForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Issue created.')
            return redirect('dashboard:newsletter')
    else:
        form = NewsletterIssueForm()
    return render(request, 'dashboard/issue_form.html', {'form': form, 'editing': False})


@login_required(login_url='/dashboard/login/')
def issue_edit(request, pk):
    obj = get_object_or_404(NewsletterIssue, pk=pk)
    if request.method == 'POST':
        form = NewsletterIssueForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Issue updated.')
            return redirect('dashboard:newsletter')
    else:
        form = NewsletterIssueForm(instance=obj)
    return render(request, 'dashboard/issue_form.html', {'form': form, 'editing': True})


@login_required(login_url='/dashboard/login/')
@require_POST
def issue_delete(request, pk):
    get_object_or_404(NewsletterIssue, pk=pk).delete()
    messages.success(request, 'Issue deleted.')
    return redirect('dashboard:newsletter')


@login_required(login_url='/dashboard/login/')
@require_POST
def subscriber_delete(request, pk):
    get_object_or_404(NewsletterSubscriber, pk=pk).delete()
    messages.success(request, 'Subscriber removed.')
    return redirect('dashboard:newsletter')


@login_required(login_url='/dashboard/login/')
@require_POST
def subscriber_toggle(request, pk):
    sub = get_object_or_404(NewsletterSubscriber, pk=pk)
    sub.is_active = not sub.is_active
    sub.save()
    messages.success(request, f'Subscriber {"activated" if sub.is_active else "deactivated"}.')
    return redirect('dashboard:newsletter')


# -------- Messages --------

@login_required(login_url='/dashboard/login/')
def message_list(request):
    return render(request, 'dashboard/messages.html', {
        'messages_list': ContactMessage.objects.all(),
        'unread_count': ContactMessage.objects.filter(is_read=False).count(),
    })


@login_required(login_url='/dashboard/login/')
@require_POST
def message_read(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    msg.is_read = True
    msg.save()
    messages.success(request, 'Marked as read.')
    return redirect('dashboard:messages')


@login_required(login_url='/dashboard/login/')
@require_POST
def message_delete(request, pk):
    get_object_or_404(ContactMessage, pk=pk).delete()
    messages.success(request, 'Message deleted.')
    return redirect('dashboard:messages')


# -------- Uses / Stack --------

@login_required(login_url='/dashboard/login/')
def uses(request):
    return render(request, 'dashboard/uses.html', {
        'categories': UsesCategory.objects.prefetch_related('items').all(),
    })


@login_required(login_url='/dashboard/login/')
def uses_category_create(request):
    if request.method == 'POST':
        form = UsesCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created.')
            return redirect('dashboard:uses')
    else:
        form = UsesCategoryForm()
    return render(request, 'dashboard/uses_category_form.html', {'form': form, 'editing': False})


@login_required(login_url='/dashboard/login/')
def uses_category_edit(request, pk):
    obj = get_object_or_404(UsesCategory, pk=pk)
    if request.method == 'POST':
        form = UsesCategoryForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated.')
            return redirect('dashboard:uses')
    else:
        form = UsesCategoryForm(instance=obj)
    return render(request, 'dashboard/uses_category_form.html', {'form': form, 'editing': True})


@login_required(login_url='/dashboard/login/')
@require_POST
def uses_category_delete(request, pk):
    get_object_or_404(UsesCategory, pk=pk).delete()
    messages.success(request, 'Category deleted.')
    return redirect('dashboard:uses')


@login_required(login_url='/dashboard/login/')
def uses_item_create(request):
    if request.method == 'POST':
        form = UsesItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item created.')
            return redirect('dashboard:uses')
    else:
        form = UsesItemForm()
    return render(request, 'dashboard/uses_item_form.html', {'form': form, 'editing': False})


@login_required(login_url='/dashboard/login/')
def uses_item_edit(request, pk):
    obj = get_object_or_404(UsesItem, pk=pk)
    if request.method == 'POST':
        form = UsesItemForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item updated.')
            return redirect('dashboard:uses')
    else:
        form = UsesItemForm(instance=obj)
    return render(request, 'dashboard/uses_item_form.html', {'form': form, 'editing': True})


@login_required(login_url='/dashboard/login/')
@require_POST
def uses_item_delete(request, pk):
    get_object_or_404(UsesItem, pk=pk).delete()
    messages.success(request, 'Item deleted.')
    return redirect('dashboard:uses')


# -------- Timeline --------

@login_required(login_url='/dashboard/login/')
def timeline(request):
    return render(request, 'dashboard/timeline.html', {
        'entries': TimelineEntry.objects.all(),
    })


@login_required(login_url='/dashboard/login/')
def timeline_create(request):
    if request.method == 'POST':
        form = TimelineEntryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Entry created.')
            return redirect('dashboard:timeline')
    else:
        form = TimelineEntryForm()
    return render(request, 'dashboard/timeline_form.html', {'form': form, 'editing': False})


@login_required(login_url='/dashboard/login/')
def timeline_edit(request, pk):
    obj = get_object_or_404(TimelineEntry, pk=pk)
    if request.method == 'POST':
        form = TimelineEntryForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Entry updated.')
            return redirect('dashboard:timeline')
    else:
        form = TimelineEntryForm(instance=obj)
    return render(request, 'dashboard/timeline_form.html', {'form': form, 'editing': True})


@login_required(login_url='/dashboard/login/')
@require_POST
def timeline_delete(request, pk):
    get_object_or_404(TimelineEntry, pk=pk).delete()
    messages.success(request, 'Entry deleted.')
    return redirect('dashboard:timeline')
